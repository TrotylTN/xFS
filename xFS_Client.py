# CSCI 5105 Project 3
# Team Member: Tiannan Zhou, Xuan Bi
# Written in Python 3

import sys, threading, os
from socket import *
from datetime import datetime
from argparse import ArgumentParser

MAX_PACKET_SIZE = 1024

def main():
    # main function
    (trackingServer, trackingPort, localPort, sharedDir) = parse_args()
    localIP = gethostbyname(gethostname())

    # open a log file
    logFile = open("{0}-{1}.log".format(localIP, localPort), 'a')
    logFile.write(str(datetime.now()) + ": Client {0}:{1} starts.\n".format(localIP, localPort))

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
    print("    exit: exit the program")
    print("You can enter the commands above anytime during running.")
    print("If you need to see help information during runtime, \
you can enter \"help\" anytime to get it.\n")

    # thread to handle CMD input
    monitorThread = threading.Thread(target=monitorCMD, args=(sSock, localIP,
        localPort, trackingServer, trackingPort, logFile, sharedDir))
    monitorThread.start()

    # start to listen incoming transmission
    print("xFS Client {0}:{1} is listening...".format(localIP, localPort))
    while True:
        pass

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

# subroutine to return the result for find request
# it will a list that contains the servers who has this file
def toTrackFind(filename, trackingServer, trackingPort, logFile):
    res = []
    # TODO
    return res

# subroutine to update current file list to the server
def toTrackUpdateList(trackingServer, trackingPort, sharedDir, logFile):
    updatedOK = False

    return updatedOK


# subroutine to download a specified file
# it will return a bool that indicate whether the downloading is successful.
def toPeerDownload(filename, trackingServer, trackingPort, sharedDir, logFile):
    serverListWithThisFile = toTrackFind(filename, trackingServer, trackingPort)
    fileOK = False
    # TODO
    return fileOK

#subroutine to get the load of a specified peer server, it will return peer load
def toPeerGetLoad(peerIP, peerPort, logFile):
    peerLoad = 0
    # TODO
    return peerIP

# the thread to monitor the command line's input
def monitorCMD(sSock, localIP, localPort, trackingServer, trackingPort, logFile, sharedDir):
    while 1:
        sentence = input()
        if sentence[:4].lower() == "exit":
            #os.getpid() returns the parent thread id, which is the id of the main program
            #an hence terminate the main program
            msg = "{0}:{1} Exit".format(localIP, localPort)
            logFile.write(str(datetime.now()) + ": {0}\n".format(msg))
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
                trackingPort, logFile)
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
