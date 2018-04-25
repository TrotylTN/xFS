# constants and methods to help build the protocol

import hashlib
from queue import Queue

MAX_PACKET_SIZE = 1024
HEADER_SIZE = 4
LENGTH_SIZE = 2
MAX_CONTECT_SIZE = MAX_PACKET_SIZE - HEADER_SIZE * 2 - LENGTH_SIZE

def compressNumber4Bytes(number):
    if number > 268435455 or number < 0:
        raise ValueError("number to be compressed larger than 4 bytes or less \
than 0")
    st = str()
    while number > 0:
        st = chr(number % 128) + st
        number //= 128
    st = (HEADER_SIZE - len(st)) * '\x00' + st
    return st.encode()

def compressLength2Bytes(l):
    if l > MAX_CONTECT_SIZE or l < 0:
        raise ValueError("length greater than MAX_CONTECT_SIZE or less than 0")
    st = str()
    while l > 0:
        st = chr(l % 128) + st
        l //= 128
    st = (LENGTH_SIZE - len(st)) * '\x00' + st
    return st.encode()

def decompressBytesNumber(bs):
    st = bs.decode()
    res = 0
    for x in st:
        res *= 128
        res += ord(x)
    return res

# {0}: filename
FIND_REQUEST = "FD{0};{1};{2}"
# {0}: filename
DOWNLOAD_REQUEST = "DL{0}"
GETLOAD_REQUEST = "GL"
UPDATELIST_REQUEST = "UD{0};{1}"

INVALID_REPLY = "IV"
# download reply data frame (all bytes):
#   4 bytes: total packets;     (0~268435455)
#   4 bytes: current packet #;  (0~268435455)
#   2 bytes: this packet length (max 1014)
#   1014 bytes: contents
# filesize limit is about 250GB due to the limit of the protocol
# 0/0/0 means invalid filename
# 0/1/0 means file does not exist
# 0/2/0 means unknown error, please see server side log
# n/0/64 stands for the SHA-512
# n/i/len for normal reply
INVALID_DL_REPLY = compressNumber4Bytes(0) + compressNumber4Bytes(0) + compressLength2Bytes(0)
NOEXIST_DL_REPLY = compressNumber4Bytes(0) + compressNumber4Bytes(1) + compressLength2Bytes(0)
UNKNOWN_DL_REPLY = compressNumber4Bytes(0) + compressNumber4Bytes(2) + compressLength2Bytes(0)
ACK_REPLY = "\x06"
NONACK_REPLY = "\x15"

def fillPacket(s):
    if len(s) > MAX_PACKET_SIZE:
        raise ValueError("packet is longer than MAX_PACKET_SIZE")
    return s + b" " * (MAX_PACKET_SIZE - len(s))

def parseDataPacket(msg):
    total_packets = decompressBytesNumber(msg[0:4])
    num_packet = decompressBytesNumber(msg[4:8])
    msg_length = decompressBytesNumber(msg[8:10])
    datacontent = msg[10:10 + msg_length]
    return total_packets, num_packet, msg_length, datacontent

def hashSHA512Bytes(s):
    return hashlib.sha512(s).digest()

def addNoise25Randomly(filecontent, logQueue):
    import random
    if random.randint(0, 100) < 25:
        # 25% probablity to generate a voice into the file
        if len(filecontent) > 0:
            filecontent = filecontent[:-256]
            msg = "!!! Added a noise into the filecontent to be sent"
            logQueue.put(msg)
            print(msg)
    return filecontent
