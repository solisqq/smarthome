from controller.device import Device
from controller.Network.JSONProtocol import JSONPacket
from PyQt5 import QtCore
import socket
import config


class WebService(Device):
    WS_HOST = "127.0.0.1"
    WS_PORT = 8665

    def __init__(self, devInfo : Device.Info):
        Device(self).__init__(self, devInfo)

    def scan():
        s = socket.socket()
        try:
            s.connect((config.WebServer.IP, config.WebServer.PORT))
            s.send((JSONPacket.ping('controller', 'webservice').toJSONString()+"\n").encode())
            return [Device.Info(config.WebServer.IP, WebService, "webservice", config.WebServer.PORT)]
        except Exception as e: pass
        return []

    @QtCore.pyqtSlot(JSONPacket)
    def _handlePacket(self, packet : JSONPacket):
        self.debug("WB received", packet.toDict())