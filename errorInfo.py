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
INFO_F_UD = ": Received Forced Update List request from {0}:{1}"
INFO_UD_OK = ": Directory \"{0}\" SHA-512 and list have been loaded into sending\
 queue to {1}:{2}"
# information for sending packets
INFO_RE_INIT = ": Total {0} packets will be sent to {1}:{2}"
INFO_RE_FINISH = ": Total {0} packets have been successfully sent to {1}:{2}"
INFO_RE_EOS = ": Session with {0}:{1} has been closed"

# client-side information
INFO_C_DL_INIT = ": Starts to download file \"{0}\""
ERROR_C_DL_NOFILE = ": Under current record, no node has file \"{0}\""
INFO_C_DL_FDSV = ": Found node {0}:{1} has file \"{2}\", start to download"
INFO_C_DL_FDSV_N = ": Found node {0}:{1} has file \"{2}\", start to download, \
this is No.{3} try due to previous failure"
INFO_C_DL_SUCC = ": File \"{0}\" from {1}:{2} downloaded successfully"
ERROR_C_DL_FILEBROKEN = ": File \"{0}\" downloaded from {1}:{2} is broken"
INFO_C_DL_AOTRY = ": Previous downloaded file \"{0}\" is broken, try another time"


INFO_C_FD_INIT = ": Starts to send Find \"{0}\" to {1}:{2}"
INFO_C_FD_FINISH = ": Received response for Find from {0}:{1}: {2}"

INFO_C_GL_INIT = ": Starts to send GetLoad request to {0}:{1}"
ERROR_C_GL_UNRE = ": Peer Node {0} is not reachable"
INFO_C_GL_RESP = ": Peer Node {0}:{1}'s current load is {2}"

INFO_C_UD_INIT = ": Starts to update list to {0}:{1} for directory \"{2}\""

# general using information or error message
ERROR_SVR_DOWN = ": Tracking server {0}:{1} has been down currently, Find and \
UpdateList cannot be used until the server re-stands up"
WARN_SVR_CL_DOWN =": Client {0}:{1} in cache is not reachable now, removed from\
 clients list."
INFO_SVR_FDPREV = ": Found connection cache, loaded the clients list: {0}"
INFO_SVR_NEWNODE = ": Request processed is from a new client {0}:{1}, write it into cache"
INFO_SVR_FD_INIT = ": Received Find requeste for \"{0}\" from {1}:{2}"
INFO_SVR_FD_RES = ": Found {0} have the file \"{1}\""
INFO_SVR_FD_OK = ": Nodes list which has File \"{0}\" has been queued for \
sending to {1}:{2}"
INFO_SVR_UP_INIT = ": Received Update List request from {0}:{1}"
INFO_SVR_UP_OK = ": Completely received Update List from Client {0}:{1} "
INFO_SVR_F_UP_SUCC = ": Forced Update List for {0}:{1} has been successfully \
executed, filelist: {2}"
