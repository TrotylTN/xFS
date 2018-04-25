# 1 client 1 server without cache:
### Enter `make tracking` in terminal

Server side
~~~
xFS Tracking Server on 192.168.3.3:5001 has been launched.
You can enter 'exit' anytime to stop the server.
~~~

### Enter `make node1` in terminal

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

### Enter `table` and `node` on server side
~~~
table
{'192.168.3.3:5101': ['.DS_Store', 'aplusb_binary_file', 'emptyfile', 'Project3.pdf', 'short_file.txt', 'src_code.cpp']}
node
['192.168.3.3:5101']
~~~

### Enter `find Project3.pdf`, a binary file locally, on client side
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

### Enter `download Project3.pdf` on client side
Client 1 side
~~~
download Project3.pdf
You already have the file locally
~~~

There's nothing happened on server side because the request has not been sent


# 0 clients and 1 server with cache:
### Enter `make tracking` in terminal
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

# 3 clients and 1 server without cache
### 1. Enter `make tracking` in terminal
### 2. Enter `make node1` in terminal
### 3. Enter `make node2` in terminal
### 4. Enter `make node5` in terminal (sharedDir for node 5 is empty)
### 5. Enter `node` and `node` on server side
Server side
~~~
node
['192.168.3.3:5101', '192.168.3.3:5102', '192.168.3.3:5105']
table
{'192.168.3.3:5101': ['.DS_Store', 'aplusb_binary_file', 'emptyfile', 'Project3.pdf', 'short_file.txt', 'src_code.cpp'], '192.168.3.3:5102': ['w1_1_post.pdf', 'w1_2_post.pdf', 'w2_1_post.pdf', 'w2_2_post.pdf', 'w3_1_post.pdf', 'w3_2_post.pdf', 'w4_1_post.pdf', 'w4_2_post.pdf', 'w5_1_post.pdf', 'w5_2_post.pdf', 'w6_1_post.pdf', 'w6_2_post.pdf', 'w7_1_post.pdf', 'w7_2_post.pdf'], '192.168.3.3:5105': ['']}
~~~
### Enter `Download Project3.pdf` in client 5
client 5 side
~~~
~~~
server side
~~~
~~~
client 1 side (it's the only node has this file)
~~~
~~~
