# CSCI 5105 Project 3
# Team Member: Tiannan Zhou, Xuan Bi
# Written in Python 3

import sys, threading, os, math, hashlib, errno, copy
from socket import *
from datetime import datetime
from argparse import ArgumentParser
from queue import Queue

# import self defined lib
from errorInfo import *
from xFSProtocol import *

thisServerLoad = 0
serverIsUp = False
logQueue = Queue()
localIP = str()
localPort = int()
latencyTable = dict()
LATENCYCONFIG = "latency.config"

def main():
    # read the config file
    global latencyTable
    conFd = open(LATENCYCONFIG, 'r')
    latencyTable = eval(conFd.read())
    conFd.close()
    # main function
    global localIP
    global localPort
    (trackingServer, trackingPort, localPort, sharedDir) = parse_args()
    localIP = gethostbyname(gethostname())
    if not os.path.isdir(sharedDir):
        print("Shared directory specified is invalid")
        exit()

    # open a log file
    try:
        os.makedirs("./log")
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise
    logFile = open("./log/{0}-{1}.log".format(localIP, localPort), 'a')
    logFile.write(str(datetime.now()) + ": Client {0}:{1} starts.\n".format(localIP, localPort))
    global thisServerLoad
    thisServerLoad = 0
    global logQueue

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
        sSock.listen(20)
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

    msg = "xFS Client on {0}:{1} has been launched.".format(localIP, localPort)
    logFile.write(str(datetime.now()) + ": " + str(msg) + '\n')
    print(msg)

    print("\nInstrcution:")
    print("    find {filename}: returns the list of nodes which store a file")
    print("    download {filename}: will download a given file into the shared folder")
    print("    getload {server} {port}: get the load at a given peer \
requested from another peer")
    print("    updatelist: will update local files' list to the tracking server")
    print("    exit: exit the program\n")
    print("xFS Client {0}:{1} is listening...\n".format(localIP, localPort))
    print("You can enter the commands above anytime during running.")
    print("If you need to see help information during runtime, \
you can enter \"help\" anytime to get it.\n")

    # thread to handle CMD input
    monitorThread = threading.Thread(target=monitorCMD, args=(sSock, localIP,
        localPort, trackingServer, trackingPort, logFile, sharedDir))
    monitorThread.start()
    # thread to write log information into file
    logOutputThread = threading.Thread(target=writeToLog, args=(logFile, logQueue))
    logOutputThread.start()

    # start to listen incoming transmission
    while True:
        conn, srcAddr = sSock.accept()
        srcIP, srcPort = srcAddr
        serverThread = threading.Thread(target=hostServer, args=(conn, srcIP,
            srcPort, sharedDir, logQueue))
        serverThread.start()

#------------------------------------------------------------------------------#
# a thread to handle incoming transmission
def hostServer(conn, srcIP, srcPort, sharedDir, logQueue):
    sSock = conn
    global thisServerLoad
    xFSrequest = sSock.recv(MAX_PACKET_SIZE).decode().strip()
    if len(xFSrequest) == 0:
        sSock.close()
        return
    xFSreply = list()
    if xFSrequest[:2] == "FD":
        # a find filename request, this request cannot be replied from client
        filename = xFSrequest[2:].strip()
        xFSreply.append(INVALID_REPLY.encode())
        msg = str(datetime.now()) + ERROR_FD.format(filename, srcIP, srcPort)
        logQueue.put(msg)
        print(msg)
    elif xFSrequest[:2] == "DL":
        # a download request
        filename = xFSrequest[2:].strip()
        toDLfile = os.path.join(sharedDir, filename)
        msg = str(datetime.now()) + INFO_DL.format(toDLfile, srcIP, srcPort)
        logQueue.put(msg)
        print(msg)
        if filename == "":
            # invalid request
            msg = str(datetime.now()) + ERROR_DL_NAME.format(filename, srcIP, srcPort)
            logQueue.put(msg)
            print(msg)
            # added a reply for error
            xFSreply.append(INVALID_DL_REPLY)
        elif not os.path.isfile(toDLfile):
            # file unreachable
            msg = str(datetime.now()) + ERROR_DL_NO.format(toDLfile, srcIP, srcPort)
            logQueue.put(msg)
            print(msg)
            # added a reply for error
            xFSreply.append(NOEXIST_DL_REPLY)
        else:
            # file can be downloaded to the requester
            # load + 1
            thisServerLoad += 1
            try:
                filefd = open(toDLfile, 'rb')
                filecontent = filefd.read()
                filefd.close()

                total_packets = math.ceil(len(filecontent) / MAX_CONTECT_SIZE)
                # make sure at least 1 packet for content will be sent
                total_packets = max(1, total_packets)
                # start to seal packet zero, SHA-512
                packet_header = compressNumber4Bytes(total_packets) + \
                    compressNumber4Bytes(0) + compressLength2Bytes(64)
                packet_content = hashSHA512Bytes(filecontent)
                # total_packets/0/64: SHA-512 for verification
                xFSreply.append(packet_header + packet_content)

                # 25% percent to add noise
                addNoise25Randomly(filecontent, logQueue)

                for i in range(total_packets):
                    this_content = filecontent[i * MAX_CONTECT_SIZE:
                        (i + 1) * MAX_CONTECT_SIZE]
                    this_header = compressNumber4Bytes(total_packets) + \
                        compressNumber4Bytes(i + 1) + \
                        compressLength2Bytes(len(this_content))
                    xFSreply.append(this_header + this_content)
                msg = str(datetime.now()) + INFO_DL_OK.format(toDLfile, srcIP, srcPort)
                logQueue.put(msg)
                print(msg)
            except error as msg:
                msg = str(datetime.now()) + ": " + str(msg)
                logQueue.put(msg)
                print(msg)
                # met error, clear the queue and fill it with UNKNOWN_DL_REPLY
                xFSreply = list()
                xFSreply.append(UNKNOWN_DL_REPLY)
            # back to original
            thisServerLoad -= 1
    elif xFSrequest[:2] == "GL":
        # a get load request
        msg = str(datetime.now()) + INFO_GL.format(srcIP, srcPort)
        logQueue.put(msg)
        print(msg)
        xFSreply.append(str(thisServerLoad).encode())
    elif xFSrequest[:2] == "UD":
        # reply the file list to the requester
        msg = str(datetime.now()) + INFO_F_UD.format(srcIP, srcPort)
        logQueue.put(msg)
        print(msg)
        # when forced to update local file list to tracking server
        # it means the server re-stands up
        global serverIsUp
        serverIsUp = True

        fileslist = [f for f in os.listdir(sharedDir) \
            if os.path.isfile(os.path.join(sharedDir, f)) and \
            checkFileName(os.path.join(sharedDir, f))]
        # encoding the list to binary
        listcontent = ";".join(fileslist).encode()
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
            msg = str(datetime.now()) + INFO_UD_OK.format(sharedDir, srcIP, srcPort)
            logQueue.put(msg)
            print(msg)
        except error as msg:
            msg = str(datetime.now()) + ": " + str(msg)
            logQueue.put(msg)
            print(msg)
            # met error, clear the queue and fill it with UNKNOWN_DL_REPLY
            xFSreply = list()
            xFSreply.append(UNKNOWN_DL_REPLY)
    else:
        msg = str(datetime.now()) + ERROR_UNKNOWN.format(xFSrequest, srcIP, srcPort)
        logQueue.put(msg)
        print(msg)
        # added a NAK reply
        xFSreply.append(NONACK_REPLY.encode())

    # send all packets in the reply queue
    msg = str(datetime.now()) + INFO_RE_INIT.format(len(xFSreply), srcIP, srcPort)
    logQueue.put(msg)
    print(msg)
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
            srcIP, srcPort)
        logQueue.put(msg)
        print(msg)
    except error as msg:
        msg = str(datetime.now()) + ": " + str(msg)
        logQueue.put(msg)
        print(msg)
    # close this connection session
    sSock.close()
    msg = str(datetime.now()) + INFO_RE_EOS.format(srcIP, srcPort)
    logQueue.put(msg)
    print(msg)
    return

#------------------------------------------------------------------------------#
def checkFileName(filename):
    if len(filename) == 0:
        # empty string
        return False
    if ';' in filename or ':' in filename:
        return False
    return True

def findSuitableServerIdx(serverList, logQueue):
    act_val = 9999
    etl_val = 9999
    cur_idx = 0
    for i in range(len(serverList)):
        [peerIP, peerPort] = serverList[i].split(':')
        peerPort = int(peerPort)
        try:
            fixedLatency = latencyTable[localPort][peerPort]
        except error as msg:
            fixedLatency = 0
        if fixedLatency + 20 < etl_val:
            cur_idx = i
            act_val = fixedLatency
            etl_val = fixedLatency + toPeerGetLoad(peerIP, peerPort, logQueue)
        elif fixedLatency > etl_val:
            pass
        else:
            peerLatency = fixedLatency + toPeerGetLoad(peerIP, peerPort, logQueue)
            if peerLatency < etl_val:
                cur_idx = i
                etl_val = peerLatency
                act_val = fixedLatency
    return cur_idx

#------------------------------------------------------------------------------#
# subroutine to return the result for find request
# it will a list that contains the servers who has this file
def toTrackFind(filename, trackingServer, trackingPort, logQueue):
    msg = str(datetime.now()) + INFO_C_FD_INIT.format(filename, trackingServer,\
        trackingPort)
    logQueue.put(msg)
    print(msg)

    res = []
    # init socket
    try:
        cSock = socket(AF_INET, SOCK_STREAM)
    except error as msg:
        cSock = None # Handle exception
        msg = str(datetime.now()) + ": " + str(msg)
        logQueue.put(msg)
        print(msg)

    try:
        cSock.settimeout(5)
        cSock.connect((trackingServer, trackingPort))
        cSock.settimeout(None)
    except error as msg:
        cSock = None # Handle exception
        msg = str(datetime.now()) + ": " + str(msg)
        logQueue.put(msg)
        print(msg)
        global serverIsUp
        serverIsUp = False

    if cSock is None:
        # If the socket cannot be opened, write into log and return False
        msg = str(datetime.now()) + ERROR_SCT_INIT
        logQueue.put(msg)
        print(msg)
        # return error code -1, stands for not getting the response
        return [ ]

    # sending request to the tracking server
    try:
        findRequest = FIND_REQUEST.format(filename, localIP, localPort)
        cSock.send(fillPacket(findRequest.encode()))
        rdata = cSock.recv(MAX_PACKET_SIZE)
        total_packets, num_packet, msg_length, datacontent = parseDataPacket(rdata)
        # do error checking, if total_packets is zero, server side met error
        if total_packets == 0:
            raise ValueError("unknown error raised on server side")
    except error as msg:
        msg = str(datetime.now()) + ": " + str(msg)
        logQueue.put(msg)
        print(msg)
        # socket error
        return [ ]
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
        res =  filecontent.decode().split(';')
        msg = str(datetime.now()) + INFO_C_FD_FINISH.format(trackingServer, \
            trackingPort)
        logQueue.put(msg)
        print(msg)
    else:
        msg = str(datetime.now()) + ": SHA512 does not match for Find's result"
        logQueue.put(msg)
        print(msg)
        return [ ]
    cSock.close()
    msg = str(datetime.now()) + INFO_RE_EOS.format(trackingServer, trackingPort)
    logQueue.put(msg)
    print(msg)
    return res

# subroutine to update current file list to the server
def toTrackUpdateList(trackingServer, trackingPort, sharedDir, logQueue):
    msg = str(datetime.now()) + INFO_C_UD_INIT.format(trackingServer, \
        trackingPort, sharedDir)
    logQueue.put(msg)
    print(msg)

    updatedOK = False

    try:
        cSock = socket(AF_INET, SOCK_STREAM)
    except error as msg:
        cSock = None # Handle exception
        msg = str(datetime.now()) + ": " + str(msg)
        logQueue.put(msg)
        print(msg)

    try:
        cSock.settimeout(5)
        cSock.connect((trackingServer, trackingPort))
        cSock.settimeout(None)
    except error as msg:
        cSock = None # Handle exception
        msg = str(datetime.now()) + ": " + str(msg)
        logQueue.put(msg)
        print(msg)
        global serverIsUp
        serverIsUp = False

    if cSock is None:
        # If the socket cannot be opened, write into log and return False
        msg = str(datetime.now()) + ERROR_SCT_INIT
        logQueue.put(msg)
        print(msg)
        # socket error
        return updatedOK
    # starts to send request to update the list
    try:
        cSock.send(fillPacket(UPDATELIST_REQUEST.format(localIP,localPort).encode()))
        # wait for an ACK to continue sending packets
        rdata = cSock.recv(MAX_PACKET_SIZE).decode().strip()
        if (rdata != ACK_REPLY):
            raise RuntimeError("received unrecognized response for Update")
    except error as msg:
        msg = str(datetime.now()) + ": " + str(msg)
        logQueue.put(msg)
        print(msg)
        return updatedOK
        # socket error
    fileslist = [f for f in os.listdir(sharedDir) \
        if os.path.isfile(os.path.join(sharedDir, f)) and \
        checkFileName(os.path.join(sharedDir, f))]
    listcontent = ";".join(fileslist).encode()
    # start to queue the update list message
    xFSreply = list()
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
        msg = str(datetime.now()) + INFO_UD_OK.format(sharedDir, \
            trackingServer, trackingPort)
        logQueue.put(msg)
        print(msg)
    except error as msg:
        msg = str(datetime.now()) + ": " + str(msg)
        logQueue.put(msg)
        print(msg)
        # met error, clear the queue and fill it with UNKNOWN_DL_REPLY
        xFSreply = list()
        xFSreply.append(UNKNOWN_DL_REPLY)
    # start to send actual list contents
    msg = str(datetime.now()) + INFO_RE_INIT.format(len(xFSreply), \
        trackingServer, trackingPort)
    logQueue.put(msg)
    print(msg)
    try:
        deleted_one = 0
        if len(xFSreply) > 1:
            # For UpdateList, send the SHA512 first
            cSock.send(fillPacket(xFSreply[0]))
            r = cSock.recv(MAX_PACKET_SIZE).decode().strip()
            if r == ACK_REPLY:
                # received ACK, send rest packets
                del xFSreply[0]
                deleted_one = 1
            else:
                raise RuntimeError("Didn't receive ACK after sending SHA512")
        # if it's error reply, directly sending this
        for x in xFSreply:
            cSock.send(fillPacket(x))
        msg = str(datetime.now()) + INFO_RE_FINISH.format(len(xFSreply) + deleted_one, \
            trackingServer, trackingPort)
        logQueue.put(msg)
        print(msg)
        updatedOK = True
    except error as msg:
        msg = str(datetime.now()) + ": " + str(msg)
        logQueue.put(msg)
        print(msg)
    # close this connection session
    cSock.close()
    msg = str(datetime.now()) + INFO_RE_EOS.format(trackingServer, trackingPort)
    logQueue.put(msg)
    print(msg)

    return updatedOK


# subroutine to download a specified file
# it will return an int that indicate whether the downloading is successful.
def toPeerDownload(filename, trackingServer, trackingPort, sharedDir, logQueue):
    msg = str(datetime.now()) + INFO_C_DL_INIT.format(filename)
    logQueue.put(msg)
    print(msg)
    global serverIsUp
    if (not serverIsUp):
        # server is down, cannot access Find request
        msg = str(datetime.now()) + ERROR_SVR_DOWN.format( \
            trackingServer, trackingPort)
        logQueue.put(msg)
        print(msg)
        # return internet error
        return False

    serverListWithThisFile = toTrackFind(filename, trackingServer, trackingPort\
        , logQueue)
    if len(serverListWithThisFile) == 0:
        # no host has this file
        msg = str(datetime.now()) + ERROR_C_DL_NOFILE.format(filename)
        logQueue.put(msg)
        print(msg)
        # no file
        return False

    tryTimeAServer = 0
    while len(serverListWithThisFile) > 0 and tryTimeAServer < 5:
        thisRoundIndex = findSuitableServerIdx(copy.copy(serverListWithThisFile), logQueue)

        tryTimeAServer += 1
        dowloadNode = copy.copy(serverListWithThisFile[thisRoundIndex])
        [downloadAddr, downloadPort] = dowloadNode.split(':')
        downloadPort = int(downloadPort)
        if tryTimeAServer == 1:
            msg = str(datetime.now()) + INFO_C_DL_FDSV.format(downloadAddr, \
                downloadPort, filename)
        else:
            msg = str(datetime.now()) + INFO_C_DL_FDSV_N.format(downloadAddr, \
                downloadPort, filename, tryTimeAServer)
        logQueue.put(msg)
        print(msg)

        try:
            cSock = socket(AF_INET, SOCK_STREAM)
        except error as msg:
            cSock = None # Handle exception
            msg = str(datetime.now()) + ": " + str(msg)
            logQueue.put(msg)
            print(msg)

        try:
            cSock.settimeout(5)
            cSock.connect((downloadAddr, downloadPort))
            cSock.settimeout(None)
        except error as msg:
            cSock = None # Handle exception
            msg = str(datetime.now()) + ": " + str(msg)
            logQueue.put(msg)
            print(msg)

        if cSock is None:
            # If the socket cannot be opened, write into log and return False
            msg = str(datetime.now()) + ERROR_SCT_INIT
            logQueue.put(msg)
            print(msg)
            # internet error, next server
            del serverListWithThisFile[thisRoundIndex]
            continue

        # cSock successfully initialized, start to connect to the server
        dlRequest = DOWNLOAD_REQUEST.format(filename)
        try:
            cSock.send(fillPacket(dlRequest.encode()))
            # wait for the first response packet
            rdata = cSock.recv(MAX_PACKET_SIZE)
            total_packets, num_packet, msg_length, datacontent = parseDataPacket(rdata)
        except error as msg:
            msg = str(datetime.now()) + ": " + str(msg)
            logQueue.put(msg)
            print(msg)
            # no need to send ACK, close this session
            cSock.close()
            msg = str(datetime.now()) + INFO_RE_EOS.format(downloadAddr, downloadPort)
            logQueue.put(msg)
            print(msg)
            # internet error, next server
            del serverListWithThisFile[thisRoundIndex]
            continue
        if total_packets == 0:
            # received an error message
            if num_packet == 0:
                # invalid filename
                msg = ": Invalid filename error has been raised on server side"
            elif num_packet == 1:
                # file is not existent on this host
                msg = ": File non-existent error has been raised on server side"
            elif num_packet == 2:
                # unknown error on the server side
                msg = ": Unknown error has been raised on server side"
            msg = str(datetime.now()) + msg
            logQueue.put(msg)
            print(msg)
            # no need to send ACK, close this session
            cSock.close()
            msg = str(datetime.now()) + INFO_RE_EOS.format(downloadAddr, downloadPort)
            logQueue.put(msg)
            print(msg)
            # file error, next server
            del serverListWithThisFile[thisRoundIndex]
            continue
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
            # this file is correctly downloaded
            # save the content into file
            toSaveFile = os.path.join(sharedDir,filename)
            saveFd = open(toSaveFile, 'wb')
            saveFd.write(filecontent)
            saveFd.close()
            msg = str(datetime.now()) + INFO_C_DL_SUCC.format(filename, \
                downloadAddr, downloadPort)
            logQueue.put(msg)
            print(msg)
            # successfully downloaded
            return True
        else:
            # this file is not the original file
            # file broken, try this server again
            msg = str(datetime.now()) + ERROR_C_DL_FILEBROKEN.format(filename, \
                downloadAddr, downloadPort)
            logQueue.put(msg)
            print(msg)
        cSock.close()
        msg = str(datetime.now()) + INFO_RE_EOS.format(downloadAddr, downloadPort)
        logQueue.put(msg)
        print(msg)
    # tried all severs or failed more than 3 times but not download successfully
    return False

#subroutine to get the load of a specified peer server, it will return peer load
def toPeerGetLoad(peerIP, peerPort, logQueue):
    peerPort = int(peerPort)
    msg = str(datetime.now()) + INFO_C_GL_INIT.format(peerIP, peerPort)
    logQueue.put(msg)
    print(msg)

    peerLoad = 0
    try:
        cSock = socket(AF_INET, SOCK_STREAM)
    except error as msg:
        cSock = None # Handle exception
        msg = str(datetime.now()) + ": " + str(msg)
        logQueue.put(msg)
        print(msg)

    try:
        cSock.settimeout(5)
        cSock.connect((peerIP, peerPort))
        cSock.settimeout(None)
    except error as msg:
        cSock = None # Handle exception
        msg = str(datetime.now()) + ": " + str(msg)
        logQueue.put(msg)
        print(msg)

    if cSock is None:
        # If the socket cannot be opened, write into log and return False
        msg = str(datetime.now()) + ERROR_SCT_INIT
        logQueue.put(msg)
        print(msg)
        # return error code -1, stands for not getting the response
        return -1

    # cSock successfully initialized, start to connect to the server
    glRequest = GETLOAD_REQUEST
    try:
        cSock.send(fillPacket(glRequest.encode()))
        rdata = cSock.recv(MAX_PACKET_SIZE).decode().strip()
        peerLoad = int(rdata)
    except error as msg:
        msg = str(datetime.now()) + ": " + str(msg)
        logQueue.put(msg)
        print(msg)
        # closing the session
        cSock.close()
        msg = str(datetime.now()) + INFO_RE_EOS.format(peerIP, peerPort)
        logQueue.put(msg)
        # met some unknown error, print the error and return
        return -1

    # closing the session
    cSock.close()
    msg = str(datetime.now()) + INFO_RE_EOS.format(peerIP, peerPort)
    logQueue.put(msg)
    print(msg)
    return peerLoad

#------------------------------------------------------------------------------#
# the thread to monitor the command line's input
def monitorCMD(sSock, localIP, localPort, trackingServer, trackingPort, logFile, sharedDir):
    global logQueue
    # update myself to the tracking server at the begining of launching
    rtn = toTrackUpdateList(trackingServer, trackingPort, sharedDir, logQueue)
    global serverIsUp
    if rtn:
        serverIsUp = True
    else:
        serverIsUp = False
    while True:
        sentence = input()
        if sentence[:4].lower() == "exit":
            #os.getpid() returns the parent thread id, which is the id of the main program
            #an hence terminate the main program
            msg = "{0}:{1} Exit".format(localIP, localPort)
            logFile.write(str(datetime.now()) + ": {0}\n".format(msg))
            logFile.flush()
            logFile.close()
            sSock.close()
            os.kill(os.getpid(),9)
        elif sentence[:4].lower() == "find":
            # find {filename}
            # get the filename
            filename = sentence[4:].strip()
            # check whether the filename is valid
            if not checkFileName(filename):
                print ("Invalid file name, file name must be longer than 0 and \
cannot contain ';' or ':' symbols.")
                continue
            if (not serverIsUp):
                # server is down, cannot access Find request
                msg = str(datetime.now()) + ERROR_SVR_DOWN.format( \
                    trackingServer, trackingPort)
                logQueue.put(msg)
                print(msg)
                # continue to next loop
                continue
            # start to actually find this filename
            serverListWithThisFile = toTrackFind(filename, trackingServer,
                trackingPort, logQueue)
            # print the response list
            print(serverListWithThisFile)

        elif sentence[:8].lower() == "download":
            # download {filename}
            filename = sentence[8:].strip()
            # check whether the filename is valid
            if not checkFileName(filename):
                print ("Invalid file name, file name must be longer than 0 and \
cannot contain ';' or ':' symbols.")
                continue
            rtnStatus = toPeerDownload(filename, trackingServer, trackingPort, \
                sharedDir, logQueue)
            tryTimeDownload = 1
            if rtnStatus == 0:
                # everything is good
                pass
            elif rtnStatus == -1 or rtnStatus == -2:
                # file error or socket broken
                # please see log for details
                pass
            elif rtnStatus == 1:
                # file broken, try to re-download
                while tryTimeDownload <= 3 and rtnStatus == 1:
                    msg = str(datetime.now()) + INFO_C_DL_AOTRY.format(filename)
                    logQueue.put(msg)
                    print(msg)
                    tryTimeDownload += 1
                    rtnStatus = toPeerDownload(filename, trackingServer, \
                        trackingPort, sharedDir, logQueue)
                    if rtnStatus == -1 or rtnStatus == -2:
                        break
            else:
                # unexpected return status, raise an error
                raise RuntimeError("toPeerDownload returned unknown status")

        elif sentence[:7].lower() == "getload":
            # getload {server} {port}
            serverAndPort = sentence[7:].strip()
            first_space_idx = serverAndPort.index(' ')
            peerIP = serverAndPort[:first_space_idx]
            peerPort = serverAndPort[first_space_idx:].strip()
            # try to get the load
            peerLoad = toPeerGetLoad(peerIP, peerPort, logQueue)
            msg = str(datetime.now()) + INFO_C_GL_RESP.format(peerIP, peerPort,\
                peerLoad)
            logQueue.put(msg)
            print(msg)
            # print the response
            if peerLoad >= 0:
                # no error
                print(peerLoad)

        elif sentence[:10].lower() == "updatelist":
            # updatelist
            if (not serverIsUp):
                # server is down, cannot access Find request
                msg = str(datetime.now()) + ERROR_SVR_DOWN.format( \
                    trackingServer, trackingPort)
                logQueue.put(msg)
                print(msg)
                # skipped to next loop
                continue
            toTrackUpdateList(trackingServer, trackingPort, sharedDir, logQueue)

        elif sentence[:4] == "help":
            # print help information
            print("\nInstrcution:")
            print("    find {filename}: returns the list of nodes which store a file")
            print("    download {filename}: will download a given file into the shared folder")
            print("    getload {server} {port}: get the load at a given peer \
requested from another peer")
            print("    updatelist: will update local files' list to the tracking server")
            print("    exit: exit the program")
            print("You can enter the commands above anytime during running.")
            print("If you need to see help information during runtime, \
you can enter \"help\" anytime to get it.\n")
        elif sentence.strip() == "":
            # empty sentence
            pass
        else:
            # any other invalid input
            print("Command cannot be recognized, try again. ")
            print("If you need help information, please enter \"help\".\n")

#------------------------------------------------------------------------------#
# a help thread to do log output
def writeToLog(logFile, logQueue):
    while True:
        logFile.write(logQueue.get() + '\n')
        logFile.flush()
    logFile.close()

def parse_args():
    parser = ArgumentParser()

    parser.add_argument('-t', '--trackingserver', type = str, default = 'localhost',
        help = "specify a remote tracking server to connect (default: localhost)")
    parser.add_argument('-p', '--trackingport', type = int, default = 5001,
        help = "specify a port on the tracking port to connect (default: 5001)")
    parser.add_argument('-l', '--localport', type = int, default = 5101,
        help = "specify a local port to send and listen (default: 5101)")
    parser.add_argument('-d', '--directory', type = str, default = './',
        help = "specify a directory to share (default: \"./\")")
    args = parser.parse_args()
    return (args.trackingserver, args.trackingport, args.localport, args.directory)

main()
