from typing import Callable, Optional
from PyQt6 import QtCore
import requests

class SmartMessage:
    msgUId = 0
    def __init__(self, destAddress : str, message : dict) -> None:
        self.destAddress = destAddress
        self.msg = message
        SmartMessage.msgUId+=1
        self.uid = SmartMessage.msgUId
        self.msg.update({'uid': self.uid})

    def request(source : str, destAddress : str, request : dict) -> "SmartMessage":
        return SmartMessage(
            destAddress,
            {
                'source': source,
                'type': 'request',
                'msg': request
            }
        )

    def respond(destAddress : str, orgUId, source : str, msg : dict) -> "SmartMessage":
        return SmartMessage(
            destAddress,
            {
                'source': source,
                'type': 'response',
                'msg': msg,
                'orgUId': orgUId,
            }
        )

    def extractResponse(response : dict) -> Optional[dict]:
        if 'type' in response.keys() and response['type'] == 'response':
            if 'msg' in response.keys():
                return response['msg']
        return None

class Server(QtCore.QThread):
    __server : "Server" = None
    class DeviceRequest:
        def __init__(self, msg : dict, device, handler : Callable):
            self.device = device
            self.handler = handler
            self.msg = SmartMessage.request("controller", device.devInfo.ip, msg)

    def __init__(self, parent : QtCore.QObject = None):
        super().__init__(parent)
        self.__buffor : list[Server.DeviceRequest] = []
        self.__devices : list = []
        self.start()

    def registerDevice(self, device):
        self.__devices.append(device)

    @QtCore.pyqtSlot()
    def run(self):
        while(True):
            if len(self.__buffor) > 0:
                resp = self.__send(self.__buffor[0].msg)
                if resp is not None:
                    self.__buffor[0].handler(resp)
                self.__buffor.pop(0)
            for device in self.__devices:
                try:
                    r = requests.get(device.devInfo.ip)
                except: pass
            self.msleep(5)

    def get():
        if Server.__server == None: Server.__server = Server()
        return Server.__server

    def __send(self, msg : SmartMessage)->Optional[dict]:
        try:
            req = requests.post(msg.destAddress, json=msg.msg)#'http://127.0.0.1:8000/requests', json={"ask":"state"})
            if req.status_code == 200:
                return req.json()
            else: return None
        except: return None

    def send(self, device, msg : dict, handler : Callable):
        self.__buffor.append(Server.DeviceRequest(msg, device, handler))

    def independentSend(msg : SmartMessage) -> Optional[dict]:
        try:
            req = requests.post(msg.destAddress, json=msg.msg)
            if req.status_code == 200:
                return SmartMessage.extractResponse(req.json())
            else: return None
        except:
            return None
