"""
JSON packet structures:
Triggers comming into the controller structure:
{
    "meta"{
        "srcName": "webservice",
        "destName": "controller",
        "msgId": "12"
    }
    "data"{
        "type": "trigger",
        "value": "1"
    }
}
Sample response to given trigger:
{
    "meta"{
        "srcName": "controller",
        "destName": "webservice",
        "msgId": "5"
    }
    "data"{
        "type": "response",
        "value": "ok",
        "responseTo": "12"
    }
}
Initializing and registering connection from device:
{
    "meta"{
        "srcName": "webservice",
        "destName": "controller",
        "msgId": "123"
    }
    "data"{
        "type": "register",
        "value": "1278" #port
    }
}

Response trom controller:
{
    "meta"{
        "srcName": "controller",
        "destName": "webservice",
        "msgId": "11"
    }
    "data"{
        "type": "response",
        "value": "ok",
        "responseTo": "123" 
    }
}
"""

import json
import sys
from typing import Any, Callable
from PyQt6 import QtCore
import socket

class JSONPacket:
    RESPONSE = "response" 
    REGISTER = "register"
    TRIGGER = "trigger"
    __MSG_ID = 0

    def __init__(self, srcName : str, destName : str, msgType : str, value : str, responseTo : str = None):
        """Available types JSONPacket.RESPONSE, JSONPacket.REGISTER, JSONPacket.TRIGGER"""
        self.srcName = srcName
        self.destName = destName
        self.msgId = JSONPacket.__getId()
        self.type = msgType
        self.value = value
        self.responseTo = responseTo

    def __getId() -> int:
        JSONPacket.__MSG_ID+=1
        return JSONPacket.__MSG_ID

    def response(value : str, response : "JSONPacket"):
        return JSONPacket(response.destName, response.srcName, JSONPacket.response, value, response.msgId)

    def register(port : int, srcName : str, destName : str):
        return JSONPacket(srcName, destName, JSONPacket.REGISTER, str(port))

    def trigger(value : str, srcName : str, destName : str):
        return JSONPacket(srcName, destName, JSONPacket.TRIGGER, value)

    def isResponseTo(self, potentialSender : "JSONPacket"):
        if potentialSender.msgId == self.responseTo and self.srcName == potentialSender.destName: return True
        return False

    def fromJsonString(jsonString : str) -> "JSONPacket":
        parsed = json.loads(jsonString)
        toRet = JSONPacket(
            parsed["meta"]["srcName"],
            parsed["meta"]["destName"],
            parsed["data"]["type"],
            parsed["data"]["value"])
        JSONPacket.__MSG_ID-=1
        toRet.msgId = int(parsed["meta"]["msgId"])
        return toRet

    def toJSONString(self) -> str:
        return json.dumps(self.toDict())

    def toDict(self) -> dict:
        return {
            "meta": {
                "srcName": self.srcName,
                "destName": self.destName,
                "msgId": self.msgId,
            },
            "data": {
                "type": self.type,
                "value": self.value
            }}

class JSONTalker(QtCore.QThread):
    def __init__(self, host, port):
        QtCore.QThread.__init__(self)
        self.daemon = True
        self.host = host
        self.port = port
        self.start()
    
    @QtCore.pyqtSlot()
    def run(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((self.host, self.port))
            s.listen()
            while True: # Accept connections from multiple clients
                print('Listening for client...')
                conn, addr = s.accept()
                print('Connection address:', addr)
                text = ''
                while True:
                    char = conn.recv(1).decode()
                    if char == '\n': break
                    else: text += char
                print("Received:", text)

    def send(host : str, port : str, packet : JSONPacket):
        toSend = packet.toJSONString()
        toSend+='\n'
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((host, port))
            s.sendall(toSend.encode())

#app = QtCore.QCoreApplication(sys.argv)
#talker = JSONTalker("127.0.0.1", 8192)
#while(True): pass
#app.exec()
