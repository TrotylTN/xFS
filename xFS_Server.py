# CSCI 5105 Project 3
# Team Member: Tiannan Zhou, Xuan Bi
# Written in Python 3

import sys, threading, os, math, hashlib, copy
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
connectedNodes = list()
CACHE_CONNECTED_FILE = "linkedNodes.cache"

def main():
    # main function
    localPort = parse_args()
    localIP = gethostbyname(gethostname())
    # open a log file
    logFile = open("{0}-{1}-tracking.log".format(localIP, localPort), 'a')
    logFile.write(str(datetime.now()) + ": Tracking Server {0}:{1} starts.\n"
        .format(localIP, localPort))
    # global
    global logQueue
    global linkQueue
    global connectedNodes

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
        for addrport in connectedNodes:
            [clientIP, clientPort] = addrport.split(':')
            clientThreads.append(threading.Thread(target=informClientsIAmBack, \
                args=(clientIP, clientPort, threadRes)))
            clientThreads[-1].start()

        # put the updated clients list into writing queue
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
        srcIP, srcPort = srcAddr
        # TODO:
        # serverThread = threading.Thread()
        # serverThread.start()


# a multi-thread function to inform clients the server has been back
def informClientsIAmBack(clientIP, clientPort, threadRes):
    clientReachable = False
    # TODO

    if clientReachable:
        threadRes.append("{0}:{1}".format(clientIP, clientPort))
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
