# information for general socket
ERROR_SCT_INIT = ": Local client socket cannot be initialized"

# information for Find
ERROR_FD = ": Received Find request \"{0}\" from {1}:{2}, invalid request for \
clients"
# information for Download
INFO_DL = ": Received Download request \"{0}\" from {1}:{2}"
INFO_DL_OK = ": File \"{0}\" SHA-512 and contents have been loaded into sending\
 queue to {1}:{2}"
ERROR_DL_NAME = ": Received invalid filename \"{0}\" from {1}:{2}"
ERROR_DL_NO = ": No local file \"{0}\" requested from {1}:{2}"
ERROR_UNKNOWN = ": Received unrecognized request \"{0}\" from {1}:{2}"
# information for GetLoad
INFO_GL = ": Received GetLoad request from {0}:{1} and queued the reply"
# information for UpdateList
INFO_UD = ": Received Update List request from {0}:{1}"
INFO_UD_OK = ": Directory \"{0}\" SHA-512 and lists have been loaded into sending\
 queue to {1}:{2}"
# information for sending packets
INFO_RE_INIT = ": Total {0} reply packets will be sent to {1}:{2}"
INFO_RE_FINISH = ": Total {0} packets have been successfully sent to {1}:{2}"
INFO_RE_EOS = ": Session with {0}:{1} has been closed"

# client-side information
ERROR_C_DL_NOFILE = ": Under current record, no node has file \"{0}\""
INFO_C_DL_FDSV = ": Found node {0}:{1} has file \"{2}\", start to download"
INFO_C_DL = ": File \"{0}\" from {1}:{2} downloaded successfully"
ERROR_C_DL_FILEBROKEN = ": File \"{0}\" downloaded from {1}:{2} is broken"
