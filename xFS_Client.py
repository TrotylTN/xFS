# CSCI 5105 Project 3
# Team Member: Tiannan Zhou, Xuan Bi
# Written in Python 3

import sys, threading, os, math, hashlib
from socket import *
from datetime import datetime
from argparse import ArgumentParser
from queue import Queue

# import self defined lib
from errorInfo import *
from xFSProtocol import *

thisServerLoad = 0
logQueue = Queue()

def main():
    # main function
    (trackingServer, trackingPort, localPort, sharedDir) = parse_args()
    localIP = gethostbyname(gethostname())
    sharedDir = sharedDir.strip("/ ") + '/'

    # open a log file
    logFile = open("{0}-{1}.log".format(localIP, localPort), 'a')
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
        toDLfile = sharedDir + filename
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
                msg = str(datetime.now()) + ": " + msg
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
        msg = str(datetime.now()) + INFO_UD.format(srcIP, srcPort)
        logQueue.put(msg)
        print(msg)
        fileslist = [f for f in os.listdir(sharedDir) \
            if os.path.isfile(os.path.join(sharedDir, f))]
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
            msg = str(datetime.now()) + ": " + msg
            logQueue.put(msg)
            print(msg)
            # met error, clear the queue and fill it with UNKNOWN_DL_REPLY
            xFSreply = list()
            xFSreply.append(UNKNOWN_DL_REPLY)
    else:
        msg = str(datetime.now()) + ERROR_UNKNOWN.format(xFSrequest, srcIP, srcPort)
        logQueue.put(msg)
        # added a NAK reply
        xFSreply.append(NONACK_REPLY.encode())

    # send all packets in the reply queue
    msg = str(datetime.now()) + INFO_RE_INIT.format(len(xFSreply), srcIP, srcPort)
    logQueue.put(msg)
    print(msg)
    try:
        if len(xFSreply) > 1:
            # For Download and UpdateList, send the SHA512 first
            sSock.send(fillPacket(xFSreply[0]))
            r = sSock.recv(MAX_PACKET_SIZE).decode().strip()
            if r == ACK_REPLY:
                # received ACK, send rest packets
                del xFSreply[0]
            else:
                raise RuntimeError("Didn't receive ACK after sending SHA512")
        for x in xFSreply:
            sSock.send(fillPacket(x))
        msg = str(datetime.now()) + INFO_RE_FINISH.format(len(xFSreply), \
            srcIP, srcPort)
        logQueue.put(msg)
        print(msg)
    except error as msg:
        msg = str(datetime.now()) + ": " + msg
        logQueue.put(msg)
        print(msg)
    # close this connection session
    sSock.close()
    msg = str(datetime.now()) + INFO_RE_EOS.format(srcIP, srcPort)
    logQueue.put(msg)
    print(msg)
    return

#------------------------------------------------------------------------------#
# a function will test whther a address is valid and reachable (return bool)
def pingAIPAddress(remoteIP):
    pingResponse = os.system("ping -c 1 {0}".format(remoteIP))
    if response == 0:
        # reachable
        return True
    else:
        return False

def checkFileName(filename):
    if len(filename) == 0:
        # empty string
        return False
    if ';' in filename or ':' in filename:
        return False
    return True

def hashSHA512Bytes(s):
    return hashlib.sha512(s).digest()

#------------------------------------------------------------------------------#
# subroutine to return the result for find request
# it will a list that contains the servers who has this file
def toTrackFind(filename, trackingServer, trackingPort, logQueue):
    res = []
    # TODO
    return res

# subroutine to update current file list to the server
def toTrackUpdateList(trackingServer, trackingPort, sharedDir, logQueue):
    updatedOK = False

    return updatedOK


# subroutine to download a specified file
# it will return a bool that indicate whether the downloading is successful.
def toPeerDownload(filename, trackingServer, trackingPort, sharedDir, logQueue):
    serverListWithThisFile = toTrackFind(filename, trackingServer, trackingPort)
    fileOK = False
    if len(serverListWithThisFile) == 0:
        # no host has this file
        msg = str(datetime.now()) + ERROR_C_DL_NOFILE.format(filename)
        logQueue.put(msg)
        print(msg)
        return False
    # TODO: to find the best server
    dowloadNode = serverListWithThisFile[0]
    [downloadAddr, downloadPort] = dowloadNode.split(':')

    try:
        cSock = socket(AF_INET, SOCK_STREAM)
    except error as msg:
        cSock = None # Handle exception
        msg = str(datetime.now()) + ": " + msg
        logQueue.put(msg)
        print(msg)

    try:
        cSock.connect((downloadAddr, downloadPort))
    except error as msg:
        cSock = None # Handle exception
        msg = str(datetime.now()) + ": " + msg
        logQueue.put(msg)
        print(msg)

    if cSock is None:
        # If the socket cannot be opened, write into log and return False
        msg = str(datetime.now()) + ERROR_SCT_INIT
        logQueue.put(msg)
        print(msg)
        return False

    # cSock successfully initialized, start to connect to the server
    dlRequest = DOWNLOAD_REQUEST.format(filename)

    # wait for the first response packet
    rdata = cSock.recv(MAX_PACKET_SIZE)
    total_packets, num_packet, msg_length, datacontent = parseDataPacket(rdata)
    if total_packets == 0:
        # received an error message
        # TODO log
        if num_packet == 0:
            # invalid filename
            pass
        elif num_packet == 1:
            # file is not existent on this host
            pass
        elif num_packet == 2:
            # unknown error on the server side
            pass
        # no need to send ACK, close this session
        cSock.close()
        msg = str(datetime.now()) + INFO_RE_EOS.format(downloadAddr, downloadPort)
        logQueue.put(msg)
        print(msg)
        return False
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
        toSaveFile = sharedDir + filename
        saveFd = open(toSaveFile, 'wb')
        saveFd.write(filecontent)
        saveFd.close()
        msg = str(datetime.now()) + INFO_C_DL.format(filename, downloadAddr, \
            downloadPort)
        logQueue.put(msg)
        print(msg)
        fileOK = True
    else:
        # this file is not the original file
        msg = str(datetime.now()) + ERROR_C_DL_FILEBROKEN.format(filename, \
            downloadAddr, downloadPort)
        logQueue.put(msg)
        print(msg)
        fileOK = False
    cSock.close()
    msg = str(datetime.now()) + INFO_RE_EOS.format(downloadAddr, downloadPort)
    logQueue.put(msg)
    print(msg)
    return fileOK

#subroutine to get the load of a specified peer server, it will return peer load
def toPeerGetLoad(peerIP, peerPort, logQueue):
    peerLoad = 0
    # TODO
    return peerIP

#------------------------------------------------------------------------------#
# the thread to monitor the command line's input
def monitorCMD(sSock, localIP, localPort, trackingServer, trackingPort, logFile, sharedDir):
    global logQueue
    while 1:
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
            # start to actually find this filename
            serverListWithThisFile = toTrackFind(filename, trackingServer,
                trackingPort, logQueue)
            print(serverListWithThisFile)

        elif sentence[:8].lower() == "download":
            # download {filename}
            filename = sentence[8:].strip()
            # check whether the filename is valid
            # TODO

        elif sentence[:7].lower() == "getload":
            # getload {server} {port}
            serverAndPort = sentence[7:].strip()
            first_space_idx = serverAndPort.index(' ')
            peerIP = serverAndPort[:first_space_idx]
            peerPort = serverAndPort[first_space_idx:].strip()
            # check the IP and Port whether they are correct
            # TODO

        elif sentence[:10].lower() == "updatelist":
            # updatelist
            # TODO
            pass

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
