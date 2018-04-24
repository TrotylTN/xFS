# CSCI 5105 Project 3
# Team Member: Tiannan Zhou, Xuan Bi
# Written in Python 3

import sys, threading, os, math, hashlib, copy, errno
from socket import *
from datetime import datetime
from argparse import ArgumentParser
from queue import Queue
from multiprocessing.pool import ThreadPool

# import self defined lib
from errorInfo import *
from xFSProtocol import *

logQueue = Queue()
linkQueue = Queue()
fileTable = dict()
connectedNodes = list()
CACHE_CONNECTED_FILE = "linkedNodes.cache"

def main():
    # main function
    localPort = parse_args()
    localIP = gethostbyname(gethostname())
    # open a log file
    try:
        os.makedirs("./log")
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise
    logFile = open("./log/{0}-{1}-tracking.log".format(localIP, localPort), 'a')
    logFile.write(str(datetime.now()) + ": Tracking Server {0}:{1} starts.\n"
        .format(localIP, localPort))
    # global
    global logQueue
    global linkQueue

    global connectedNodes
    global fileTable

    # bind a socket
    socket_created = True
    try:
        #create a socket object, SOCK_STREAM for TCP
        sSock = socket(AF_INET, SOCK_STREAM)
    except error as msg:
        # Handle exception
        socket_created = False
        print(msg)
        logFile.write(str(datetime.now()) + ": " + str(msg) + '\n')
    try:
        #bind socket to the current address on port 5001
        sSock.bind(("localhost", localPort))
        #Listen on the given socket maximum number of connections queued is 20
        sSock.listen(30)
    except error as msg:
        # Handle exception
        socket_created = False
        print(msg)
        logFile.write(str(datetime.now()) + ": " + str(msg) + '\n')
    if not socket_created:
        # if the socket didn't bind properly, quit
        print("xFS Client: Error in Binding Socket. See log for details")
        logFile.write(str(datetime.now()) + ": Server quit with error.\n")
        logFile.close()
        quit()

    msg = "xFS Tracking Server on {0}:{1} has been launched.".\
        format(localIP, localPort)
    logFile.write(str(datetime.now()) + ": " + str(msg) + '\n')
    print(msg)
    print("You can enter 'exit' anytime to stop the server.")

    # detect whether we've had a cache
    if os.path.isfile(CACHE_CONNECTED_FILE):
        # the cahce is existent
        cacheFd = open(CACHE_CONNECTED_FILE, 'r')
        # use the cache to
        connectedNodes = eval(cacheFd.read())
        cacheFd.close()
        threadRes = list()
        clientThreads = list()
        # logging the cache
        msg = str(datetime.now()) + INFO_SVR_FDPREV.format(connectedNodes)
        logQueue.put(msg)
        print(msg)
        for addrport in connectedNodes:
            [clientIP, clientPort] = addrport.split(':')
            clientThreads.append(threading.Thread(target=informClientsIAmBack, \
                args=(clientIP, int(clientPort), threadRes)))
            clientThreads[-1].start()

        # put the updated clients list into writing queue
        for i in range(len(clientThreads)):
            clientThreads[i].join()
        connectedNodes = copy.copy(threadRes)
        linkQueue.put(copy.copy(connectedNodes))
    else:
        # the cache is not existent, create one
        cacheFd = open(CACHE_CONNECTED_FILE, 'w')
        cacheFd.write(str([ ]))
        cacheFd.flush()
        cacheFd.close()

    # start to use two threads to do log and writing to cache
    logOutputThread = threading.Thread(target=writeToLog, args=(logFile, logQueue))
    logOutputThread.start()
    writeToCacheThread = threading.Thread(target=writeToCache, args=())
    writeToCacheThread.start()
    # use another thread to handle the exit stuff
    monitorQuitThread = threading.Thread(target=monitorQuit, args=(sSock,\
        localIP, localPort, logFile))
    monitorQuitThread.start()

    # start to listen incoming transmission
    while True:
        conn, srcAddr = sSock.accept()
        serverThread = threading.Thread(target=trackingServerHost, args=(conn, srcAddr))
        serverThread.start()


def trackingServerHost(conn, srcAddr):
    sSock = conn
    global connectedNodes
    global fileTable
    global linkQueue
    global logQueue
    xFSrequest = sSock.recv(MAX_PACKET_SIZE).decode().strip()
    if len(xFSrequest) == 0:
        sSock.close()
        return
    clientIP = "unknown"
    clientPort = 0000
    if xFSrequest[:2] == "FD":
        # Find request
        [filename,clientIP,clientPort] = xFSrequest[2:].strip().split(";")
        clientPort = int(clientPort)
        msg = str(datetime.now()) + INFO_SVR_FD_INIT.format(filename, clientIP,\
            clientPort)
        logQueue.put(msg)
        print(msg)
        hostsHaveFile = list()
        for c in connectedNodes:
            if filename in fileTable[c]:
                hostsHaveFile.append(c)
        msg = str(datetime.now()) + INFO_SVR_FD_RES.format(hostsHaveFile, filename)
        # # OPTIMIZE: can test the host having the file, or do this on client side
        xFSreply = []
        listcontent = ";".join(hostsHaveFile).encode()
        try:
            total_packets = math.ceil(len(listcontent) / MAX_CONTECT_SIZE)
            # make sure at least 1 packet for content will be sent
            total_packets = max(1, total_packets)
            # start to seal packet zero, SHA-512
            packet_header = compressNumber4Bytes(total_packets) + \
                compressNumber4Bytes(0) + compressLength2Bytes(64)
            packet_content = hashSHA512Bytes(listcontent)
            # total_packets/0/64: SHA-512 for verification
            xFSreply.append(packet_header + packet_content)

            for i in range(total_packets):
                this_content = listcontent[i * MAX_CONTECT_SIZE:
                    (i + 1) * MAX_CONTECT_SIZE]
                this_header = compressNumber4Bytes(total_packets) + \
                    compressNumber4Bytes(i + 1) + \
                    compressLength2Bytes(len(this_content))
                xFSreply.append(this_header + this_content)
            msg = str(datetime.now()) + INFO_SVR_FD_OK.format(filename, clientIP, \
                clientPort)
            logQueue.put(msg)
            print(msg)
        except error as msg:
            msg = str(datetime.now()) + ": " + str(msg)
            logQueue.put(msg)
            print(msg)
            # met error, clear the queue and fill it with UNKNOWN_DL_REPLY
            xFSreply = list()
            xFSreply.append(UNKNOWN_DL_REPLY)
        try:
            deleted_one = 0
            if len(xFSreply) > 1:
                # For Download and UpdateList, send the SHA512 first
                sSock.send(fillPacket(xFSreply[0]))
                r = sSock.recv(MAX_PACKET_SIZE).decode().strip()
                if r == ACK_REPLY:
                    # received ACK, send rest packets
                    del xFSreply[0]
                    deleted_one = 1
                else:
                    raise RuntimeError("Didn't receive ACK after sending SHA512")
            for x in xFSreply:
                sSock.send(fillPacket(x))
            msg = str(datetime.now()) + INFO_RE_FINISH.format(len(xFSreply) + deleted_one, \
                clientIP, clientPort)
            logQueue.put(msg)
            print(msg)
        except error as msg:
            msg = str(datetime.now()) + ": " + str(msg)
            logQueue.put(msg)
            print(msg)

    elif xFSrequest[:2] == "UD":
        # update
        [clientIP, clientPort] = xFSrequest[2:].strip().split(";")
        clientPort = int(clientPort)
        msg = str(datetime.now()) + INFO_SVR_UP_INIT.format(clientIP, clientPort)
        logQueue.put(msg)
        print(msg)
        # send ACK back to client, let it continue
        sSock.send(fillPacket(ACK_REPLY.encode()))
        try:
            rdata = sSock.recv(MAX_PACKET_SIZE)
            total_packets, num_packet, msg_length, datacontent = parseDataPacket(rdata)
            # do error checking, if total_packets is zero, server side met error
            if total_packets == 0:
                raise ValueError("unknown error raised on server side")
        except error as msg:
            msg = str(datetime.now()) + ": " + str(msg)
            logQueue.put(msg)
            print(msg)
        if num_packet == 0 and len(datacontent) == 64:
            origSHA512 = datacontent
        else:
            raise ValueError("SHA512's number & length does not match")
        contentCache = [None] * (total_packets + 1)
        # send ACK to the server
        sSock.send(fillPacket(ACK_REPLY.encode()))
        # cache all the contents regardless of receiving order
        # it can be optimized
        for i in range(total_packets):
            rdata = sSock.recv(MAX_PACKET_SIZE)
            tot, num_packet, msg_length, datacontent = parseDataPacket(rdata)
            contentCache[num_packet] = datacontent
        filecontent = bytes()
        for i in range(1, total_packets + 1):
            filecontent += contentCache[i]
        if hashSHA512Bytes(filecontent) == origSHA512:
            filelist = filecontent.decode().split(";")
            addrport = "{0}:{1}".format(clientIP, clientPort)
            fileTable[addrport] = copy.copy(filelist)
            msg = str(datetime.now()) + INFO_SVR_UP_OK.format(clientIP, clientPort)
            logQueue.put(msg)
            print(msg)
            print(filelist)
        else:
            msg = str(datetime.now()) + ": SHA512 does not match for Update's result"
            logQueue.put(msg)
            print(msg)
    else:
        # unrecognized request
        msg = str(datetime.now()) + ERROR_UNKNOWN.format(xFSrequest, clientIP, clientPort)
        logQueue.put(msg)
        print(msg)
        # added a NAK reply
        sSock.send(fillPacket(NONACK_REPLY.encode()))
        # close this connection session
        sSock.close()
        msg = str(datetime.now()) + INFO_RE_EOS.format(clientIP, clientPort)
        logQueue.put(msg)
        print(msg)
        return
    # close this connection session
    sSock.close()
    msg = str(datetime.now()) + INFO_RE_EOS.format(clientIP, clientPort)
    logQueue.put(msg)
    print(msg)
    # added the new client into client list
    addrport = "{0}:{1}".format(clientIP, clientPort)
    if not addrport in connectedNodes:
        connectedNodes.append(addrport)
        # clear the file list
        fileTable[addrport] = []
        linkQueue.put(copy.copy(connectedNodes))
        msg = str(datetime.now()) + INFO_SVR_NEWNODE.format(clientIP, clientPort)
        logQueue.put(msg)
        print(msg)
    return



# a multi-thread function to inform clients the server has been back
def informClientsIAmBack(clientIP, clientPort, threadRes):
    clientPort = int(clientPort)
    clientReachable = False
    global fileTable
    global logQueue

    try:
        cSock = socket(AF_INET, SOCK_STREAM)
    except error as msg:
        cSock = None # Handle exception
        msg = str(datetime.now()) + ": " + str(msg)
        logQueue.put(msg)
        print(msg)

    try:
        cSock.settimeout(5)
        cSock.connect((clientIP, clientPort))
        cSock.settimeout(None)
    except error as msg:
        cSock = None # Handle exception
        msg = str(datetime.now()) + ": " + str(msg)
        logQueue.put(msg)
        print(msg)

    if cSock is None:
        # If the client connection cannot be opened, write into log and return
        msg = str(datetime.now()) + WARN_SVR_CL_DOWN.format(clientIP, clientPort)
        logQueue.put(msg)
        print(msg)
        # return here, we are sure that this client has been down
        return

    # client is reachable, connection has been built
    clientReachable = True
    # append this node into table
    threadRes.append("{0}:{1}".format(clientIP, clientPort))
    addrport = "{0}:{1}".format(clientIP, clientPort)
    # start to send force update
    try:
        forcedUpdateRequest = UPDATELIST_REQUEST[:2]
        cSock.send(fillPacket(forcedUpdateRequest.encode()))
        rdata = cSock.recv(MAX_PACKET_SIZE)
        total_packets, num_packet, msg_length, datacontent = parseDataPacket(rdata)
    except error as msg:
        msg = str(datetime.now()) + ": " + str(msg)
        logQueue.put(msg)
        print(msg)
        # socket error
        return
    if total_packets == 0:
        msg = ": Unknown error has been raised on client side"
        msg = str(datetime.now()) + msg
        logQueue.put(msg)
        print(msg)
        cSock.close()
        msg = str(datetime.now()) + INFO_RE_EOS.format(downloadAddr, downloadPort)
        logQueue.put(msg)
        print(msg)
        return
    # prepare to receive the data content
    if num_packet == 0 and len(datacontent) == 64:
        origSHA512 = datacontent
    else:
        raise ValueError("SHA512's number & length does not match")
    contentCache = [None] * (total_packets + 1)
    # send ACK to the server
    cSock.send(fillPacket(ACK_REPLY.encode()))
    # cache all the contents regardless of receiving order
    # it can be optimized
    for i in range(total_packets):
        rdata = cSock.recv(MAX_PACKET_SIZE)
        tot, num_packet, msg_length, datacontent = parseDataPacket(rdata)
        contentCache[num_packet] = datacontent
    filecontent = bytes()
    for i in range(1, total_packets + 1):
        filecontent += contentCache[i]
    if hashSHA512Bytes(filecontent) == origSHA512:
        # this content is correctly downloaded
        # save the content into file name table
        filelist = filecontent.decode().split(";")
        fileTable[addrport] = copy.copy(filelist)
    else:
        # this content is not the original one
        raise RuntimeError("content received is broken")

    # close the session
    cSock.close()
    msg = str(datetime.now()) + INFO_RE_EOS.format(clientIP, clientPort)
    logQueue.put(msg)
    print(msg)
    return

def writeToCache():
    global linkQueue
    while True:
        new_list = linkQueue.get()
        cacheFile = open(CACHE_CONNECTED_FILE, 'w')
        cacheFile.write(str(new_list))
        cacheFile.flush()
        cacheFile.close()

def writeToLog(logFile, logQueue):
    while True:
        logFile.write(logQueue.get() + '\n')
        logFile.flush()
    logFile.close()

def parse_args():
    parser = ArgumentParser()

    parser.add_argument('-p', '--localport', type = int, default = 5001,
        help = "specify a local port for tracking server (default: 5001)")

    args = parser.parse_args()
    return args.localport

def monitorQuit(sSock, localIP, localPort, logFile):
    while 1:
        sentence = input()
        if sentence[:4].lower() == "exit":
            #os.getpid() returns the parent thread id, which is the id of the main program
            #an hence terminate the main program
            msg = "{0}:{1} Tracking server exit".format(localIP, localPort)
            logFile.write(str(datetime.now()) + ": {0}\n".format(msg))
            logFile.flush()
            logFile.close()
            sSock.close()
            os.kill(os.getpid(),9)

main()
