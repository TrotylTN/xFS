# Testcase for Project 3
### A. 1 client 1 server without cache:
##### Enter `make tracking` in terminal

Server side
~~~
xFS Tracking Server on 192.168.3.3:5001 has been launched.
You can enter 'exit' anytime to stop the server.
~~~

##### Enter `make node1` in terminal

Client 1 side

~~~
xFS Client on 192.168.3.3:5101 has been launched.

Instrcution:
    find {filename}: returns the list of nodes which store a file
    download {filename}: will download a given file into the shared folder
    getload {server} {port}: get the load at a given peer requested from another peer
    updatelist: will update local files' list to the tracking server
    exit: exit the program

xFS Client 192.168.3.3:5101 is listening...

You can enter the commands above anytime during running.
If you need to see help information during runtime, you can enter "help" anytime to get it.

2018-04-24 22:18:14.466031: Starts to update list to 127.0.0.1:5001 for directory "./node1_shareDir"
2018-04-24 22:18:14.467145: Directory "./node1_shareDir" SHA-512 and list have been loaded into sending queue to 127.0.0.1:5001
2018-04-24 22:18:14.467199: Total 2 packets will be sent to 127.0.0.1:5001
2018-04-24 22:18:14.467406: Total 2 packets have been successfully sent to 127.0.0.1:5001
2018-04-24 22:18:14.467520: Session with 127.0.0.1:5001 has been closed
~~~

Server side
~~~
2018-04-24 22:18:14.466666: Received Update List request from 192.168.3.3:5101
2018-04-24 22:18:14.467542: Forced Update List for 192.168.3.3:5101 has been successfully executed, filelist: ['.DS_Store', 'aplusb_binary_file', 'emptyfile', 'Project3.pdf', 'short_file.txt', 'src_code.cpp']
2018-04-24 22:18:14.467661: Session with 192.168.3.3:5101 has been closed
2018-04-24 22:18:14.467825: Request processed is from a new client 192.168.3.3:5101, write it into cache
~~~

##### Enter `table` and `node` on server side
~~~
table
{'192.168.3.3:5101': ['.DS_Store', 'aplusb_binary_file', 'emptyfile', 'Project3.pdf', 'short_file.txt', 'src_code.cpp']}
node
['192.168.3.3:5101']
~~~

##### Enter `find Project3.pdf`, a binary file locally, on client side
Client 1 side
~~~
find Project3.pdf
2018-04-24 22:35:51.439572: Starts to send Find "Project3.pdf" to 127.0.0.1:5001
2018-04-24 22:35:51.440663: Received response for Find from 127.0.0.1:5001: ['192.168.3.3:5101']
2018-04-24 22:35:51.440767: Session with 127.0.0.1:5001 has been closed
['192.168.3.3:5101']
~~~
Server side
~~~
2018-04-24 22:27:39.293604: Received Find requeste for "Project3.pdf" from 192.168.3.3:5101
2018-04-24 22:27:39.293817: Nodes list which has File "Project3.pdf" has been queued for sending to 192.168.3.3:5101
2018-04-24 22:27:39.294049: Total 2 packets have been successfully sent to 192.168.3.3:5101
2018-04-24 22:27:39.294137: Session with 192.168.3.3:5101 has been closed
~~~

##### Enter `download Project3.pdf` on client side
Client 1 side
~~~
download Project3.pdf
You already have the file locally
~~~

There's nothing happened on server side because the request has not been sent


### B. 0 clients and 1 server with cache:
##### Enter `make tracking` in terminal
~~~
xFS Tracking Server on 192.168.3.3:5001 has been launched.
You can enter 'exit' anytime to stop the server.
2018-04-24 22:14:25.361484: Found connection cache, loaded the clients list: ['192.168.3.3:5101', '192.168.3.3:5102', '192.168.3.3:5105']
2018-04-24 22:14:25.362358: [Errno 61] Connection refused
2018-04-24 22:14:25.362539: Client 192.168.3.3:5101 in cache is not reachable now, removed from clients list.
2018-04-24 22:14:25.362826: [Errno 61] Connection refused
2018-04-24 22:14:25.363081: Client 192.168.3.3:5102 in cache is not reachable now, removed from clients list.
2018-04-24 22:14:25.363129: [Errno 61] Connection refused
2018-04-24 22:14:25.363220: Client 192.168.3.3:5105 in cache is not reachable now, removed from clients list.
~~~

The server will find out that the clients in file have gone, then remove them from the `connectedNodes` list

### C. 2 clients and 0 server with cache:
##### 1. Enter `make node1` in terminal
##### 2. Enter `make node2` in terminal
##### 3. Try all operations in Client 1
Client 1 side:
~~~
2018-04-24 23:11:11.158143: Starts to update list to 127.0.0.1:5001 for directory "./node1_shareDir"
2018-04-24 23:11:11.158834: [Errno 61] Connection refused
2018-04-24 23:11:11.158885: Local client socket cannot be initialized
find w1_1_post.pdf
2018-04-24 23:11:44.055938: Tracking server 127.0.0.1:5001 has been down currently, Find and UpdateList cannot be used until the server re-stands up
updatelist
2018-04-24 23:11:48.271839: Tracking server 127.0.0.1:5001 has been down currently, Find and UpdateList cannot be used until the server re-stands up
download w1_1_post.pdf
2018-04-24 23:15:49.460518: Starts to download file "w1_1_post.pdf"
2018-04-24 23:15:49.461400: Tracking server 127.0.0.1:5001 has been down currently, Find and UpdateList cannot be used until the server re-stands up
Failed to dowload, see logs for details
getload Localhost 5102
2018-04-24 23:16:29.572325: Starts to send GetLoad request to Localhost:5102
2018-04-24 23:16:29.573987: Peer Localhost:5102's load: 0
2018-04-24 23:16:29.574234: Session with Localhost:5102 has been closed
2018-04-24 23:16:29.574343: Peer Node Localhost:5102's current load is 0
0
~~~
After the Client 1 has been launched, it found the server is not available. So it will disable the functionality related to the tracking server (all operations except GetLoad) until the server is back.

### D. 3 clients and 1 server
##### 1. Enter `make tracking` in terminal
##### 2. Enter `make node1` in terminal
##### 3. Enter `make node2` in terminal
##### 4. Enter `make node5` in terminal (sharedDir for node 5 is empty)
##### 5. Enter `node` and `node` on server side
Server side
~~~
node
['192.168.3.3:5101', '192.168.3.3:5102', '192.168.3.3:5105']
table
{'192.168.3.3:5101': ['.DS_Store', 'aplusb_binary_file', 'emptyfile', 'Project3.pdf', 'short_file.txt', 'src_code.cpp'], '192.168.3.3:5102': ['w1_1_post.pdf', 'w1_2_post.pdf', 'w2_1_post.pdf', 'w2_2_post.pdf', 'w3_1_post.pdf', 'w3_2_post.pdf', 'w4_1_post.pdf', 'w4_2_post.pdf', 'w5_1_post.pdf', 'w5_2_post.pdf', 'w6_1_post.pdf', 'w6_2_post.pdf', 'w7_1_post.pdf', 'w7_2_post.pdf'], '192.168.3.3:5105': ['']}
~~~

##### Enter `GetLoad 192.168.3.3 5102` in client 5
client 5 side
~~~
GetLoad 192.168.3.3 5102
2018-04-24 22:51:05.835913: Starts to send GetLoad request to 192.168.3.3:5102
2018-04-24 22:51:05.836908: Peer 192.168.3.3:5102's load: 0
2018-04-24 22:51:05.837028: Session with 192.168.3.3:5102 has been closed
2018-04-24 22:51:05.837070: Peer Node 192.168.3.3:5102's current load is 0
0
~~~

client 2 side
~~~
2018-04-24 22:51:05.836648: Received GetLoad request from 192.168.3.3:53615 and queued the reply
2018-04-24 22:51:05.836776: Total 1 packets will be sent to 192.168.3.3:53615
2018-04-24 22:51:05.836885: Total 1 packets have been successfully sent to 192.168.3.3:53615
2018-04-24 22:51:05.836994: Session with 192.168.3.3:53615 has been closed
~~~

##### Enter `Download Project3.pdf` in client 5
client 5 side
~~~
download Project3.pdf
2018-04-24 22:47:39.931897: Starts to download file "Project3.pdf"
2018-04-24 22:47:39.932011: Starts to send Find "Project3.pdf" to 127.0.0.1:5001
2018-04-24 22:47:39.933031: Received response for Find from 127.0.0.1:5001: ['192.168.3.3:5101']
2018-04-24 22:47:39.933203: Session with 127.0.0.1:5001 has been closed
2018-04-24 22:47:39.933291: Starts to send GetLoad request to 192.168.3.3:5101
2018-04-24 22:47:39.934101: Peer 192.168.3.3:5101's load: 0
2018-04-24 22:47:39.934220: Session with 192.168.3.3:5101 has been closed
2018-04-24 22:47:39.934353: Found node 192.168.3.3:5101 has file "Project3.pdf", start to download
2018-04-24 22:47:39.947531: File "Project3.pdf" from 192.168.3.3:5101 downloaded successfully
Successfully downloaded
~~~

server side
~~~
2018-04-24 22:47:39.932506: Received Find requeste for "Project3.pdf" from 192.168.3.3:5105
2018-04-24 22:47:39.932668: Nodes list which has File "Project3.pdf" has been queued for sending to 192.168.3.3:5105
2018-04-24 22:47:39.932951: Total 2 packets have been successfully sent to 192.168.3.3:5105
2018-04-24 22:47:39.933092: Session with 192.168.3.3:5105 has been closed
~~~
client 1 side (it's the only node has this file)
~~~
2018-04-24 22:47:39.933845: Received GetLoad request from 192.168.3.3:53525 and queued the reply
2018-04-24 22:47:39.933960: Total 1 packets will be sent to 192.168.3.3:53525
2018-04-24 22:47:39.934019: Total 1 packets have been successfully sent to 192.168.3.3:53525
2018-04-24 22:47:39.934097: Session with 192.168.3.3:53525 has been closed
2018-04-24 22:47:39.934907: Received Download request "./node1_shareDir/Project3.pdf" from 192.168.3.3:53526
2018-04-24 22:47:39.943334: File "./node1_shareDir/Project3.pdf" SHA-512 and contents have been loaded into sending queue to 192.168.3.3:53526
2018-04-24 22:47:39.943462: Total 141 packets will be sent to 192.168.3.3:53526
2018-04-24 22:47:39.944467: Total 141 packets have been successfully sent to 192.168.3.3:53526
2018-04-24 22:47:39.944671: Session with 192.168.3.3:53526 has been closed
~~~
##### Leave all clients but Kill the Server, then enter `make tracking` in terminal to re-open the Server
Server side
~~~
xFS Tracking Server on 192.168.3.3:5001 has been launched.
You can enter 'exit' anytime to stop the server.
2018-04-24 22:56:14.931769: Found connection cache, loaded the clients list: ['192.168.3.3:5101', '192.168.3.3:5102', '192.168.3.3:5105']
2018-04-24 22:56:14.934287: Forced Update List for 192.168.3.3:5101 has been successfully executed, filelist: ['.DS_Store', 'aplusb_binary_file', 'emptyfile', 'Project3.pdf', 'short_file.txt', 'src_code.cpp']
2018-04-24 22:56:14.934468: Session with 192.168.3.3:5101 has been closed
2018-04-24 22:56:14.934991: Forced Update List for 192.168.3.3:5102 has been successfully executed, filelist: ['.DS_Store', 'w1_1_post.pdf', 'w1_2_post.pdf', 'w2_1_post.pdf', 'w2_2_post.pdf', 'w3_1_post.pdf', 'w3_2_post.pdf', 'w4_1_post.pdf', 'w4_2_post.pdf', 'w5_1_post.pdf', 'w5_2_post.pdf', 'w6_1_post.pdf', 'w6_2_post.pdf', 'w7_1_post.pdf', 'w7_2_post.pdf']
2018-04-24 22:56:14.935162: Session with 192.168.3.3:5102 has been closed
2018-04-24 22:56:14.936383: Forced Update List for 192.168.3.3:5105 has been successfully executed, filelist: ['.DS_Store', 'Project3.pdf']
2018-04-24 22:56:14.936513: Session with 192.168.3.3:5105 has been closed
~~~
##### Enter `node` and `table` on server side after restart
~~~
node
['192.168.3.3:5101', '192.168.3.3:5102', '192.168.3.3:5105']
table
{'192.168.3.3:5101': ['.DS_Store', 'aplusb_binary_file', 'emptyfile', 'Project3.pdf', 'short_file.txt', 'src_code.cpp'], '192.168.3.3:5102': ['.DS_Store', 'w1_1_post.pdf', 'w1_2_post.pdf', 'w2_1_post.pdf', 'w2_2_post.pdf', 'w3_1_post.pdf', 'w3_2_post.pdf', 'w4_1_post.pdf', 'w4_2_post.pdf', 'w5_1_post.pdf', 'w5_2_post.pdf', 'w6_1_post.pdf', 'w6_2_post.pdf', 'w7_1_post.pdf', 'w7_2_post.pdf'], '192.168.3.3:5105': ['.DS_Store', 'Project3.pdf']}
~~~
It's obviously that the server will re-connect with the clients and force them to `Update List` to get their updated file list.

##### Enter `download Project3.pdf` in client 2 (Now client 1 and 5 both have this file)
client 2 side
~~~
download Project3.pdf
2018-04-24 23:01:26.203049: Starts to download file "Project3.pdf"
2018-04-24 23:01:26.204224: Starts to send Find "Project3.pdf" to 127.0.0.1:5001
2018-04-24 23:01:26.208468: Received response for Find from 127.0.0.1:5001: ['192.168.3.3:5101', '192.168.3.3:5105']
2018-04-24 23:01:26.208720: Session with 127.0.0.1:5001 has been closed
2018-04-24 23:01:26.208971: Starts to send GetLoad request to 192.168.3.3:5101
2018-04-24 23:01:26.212774: Peer 192.168.3.3:5101's load: 0
2018-04-24 23:01:26.213074: Session with 192.168.3.3:5101 has been closed
2018-04-24 23:01:26.213196: Starts to send GetLoad request to 192.168.3.3:5105
2018-04-24 23:01:26.216444: Peer 192.168.3.3:5105's load: 0
2018-04-24 23:01:26.216632: Session with 192.168.3.3:5105 has been closed
2018-04-24 23:01:26.216752: Found node 192.168.3.3:5105 has file "Project3.pdf", start to download
2018-04-24 23:01:49.417454: Invalid filename error has been raised on server side
2018-04-24 23:01:49.417677: Session with 192.168.3.3:5105 has been closed
2018-04-24 23:01:49.417778: Starts to send GetLoad request to 192.168.3.3:5101
2018-04-24 23:01:49.419029: Peer 192.168.3.3:5101's load: 0
2018-04-24 23:01:49.419107: Session with 192.168.3.3:5101 has been closed
2018-04-24 23:01:49.419150: Found node 192.168.3.3:5101 has file "Project3.pdf", start to download, this is No.2 try due to previous failure
2018-04-24 23:01:49.430781: File "Project3.pdf" from 192.168.3.3:5101 downloaded successfully
Successfully downloaded
~~~
Client 2 tried to download the file from client 5 first due to the given latency table and our node selection algorithm based on latency & load, but client 5 was crashed during this peroid (we manually did it). After Client 2 detected the first try failed, it started to try to download it from Client 1. And it's successful eventually. (Actually we set the maximum automatic re-try time is 5 times)
### E. Download
