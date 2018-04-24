# this project has been implemented in python3
PY = python3

all:
	@echo "use \"make node[1-5]\" or \"make tracking\" to start clients or servers "

tracking:
	${PY} xFS_Server.py

node1:
	${PY} xFS_Client.py -d "./node1_shareDir" -l 5101

node2:
	${PY} xFS_Client.py -d "./node2_shareDir" -l 5102

node3:
	${PY} xFS_Client.py -d "./node3_shareDir" -l 5103

node4:
	${PY} xFS_Client.py -d "./node4_shareDir" -l 5104

node5:
	${PY} xFS_Client.py -d "./node1_shareDir" -l 5105
