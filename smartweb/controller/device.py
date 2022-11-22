from typing import Any
from PyQt6 import QtWidgets, QtCore
from controller.Network.JSONProtocol import JSONPacket
import config
from controller.trigger import Trigger

class Device(QtWidgets.QWidget):
    nameChanged = QtCore.pyqtSignal(str)
    disconnected = QtCore.pyqtSignal(object)
    connectionBack = QtCore.pyqtSignal(object)
    __trigger = QtCore.pyqtSignal(int, object)

    class Info:
        def __init__(self, ip : str, devType : type, id : str, port : int):
            self.ip = ip
            self.devType = devType
            self.port = port
            self.id = id

        def getInfo(self) -> dict:
            return {"ip": self.ip, "btype": self.devType, "id": self.id, "port": self.port}

        def __str__(self) -> str:
            return str(self.getInfo())
        
        def instantiate(self) -> "Device":
            return self.devType(self)

    def __init__(self, info : Info):
        QtWidgets.QWidget.__init__(self)
        config.Debuggable.__init__(self, info.id)
        self.info = info
        self.debug = config.Debuggable(self.info.id)
        self._connected = True

        self.trigger = Trigger()
        self.__trigger.connect(self.trigger.handle)

        self._checkConnectionTimer = QtCore.QTimer()
        self._checkConnectionTimer.timeout.connect(self.__connectionFailed)
        self._checkConnectionTimer.start(config.Device.CONNECTION_TIMEOUT_MS)
        self.setLayout(QtWidgets.QVBoxLayout())
        self.layout().addWidget(QtWidgets.QLabel("Name:"))
        self._nameEdit = QtWidgets.QLineEdit()
        self.layout().addWidget(self._nameEdit)
        self._nameEdit.textChanged.connect(lambda text: self.nameChanged.emit(text))
        self._nameEdit.textChanged.connect(self.debug._setName)

    def __connectionFailed(self):
        self._connected = False
        self.disconnected.emit(self)

    def reasureConnection(self):
        if(self._connected==False):
            self.connectionBack.emit(self)
        self._connected = True
        self._checkConnectionTimer.stop()
        self._checkConnectionTimer.start(config.Device.CONNECTION_TIMEOUT_MS)

    def getName(self) -> str: return self._nameEdit.text()
    def setName(self, newName : str): self._nameEdit.setText(newName)

    def __getAllSubclasses(someClass : type) -> list[type]:
        all_subclasses = []
        for subclass in someClass.__subclasses__():
            all_subclasses.append(subclass)
            all_subclasses.extend(Device.__getAllSubclasses(subclass))

        return all_subclasses

    def scan() -> list[Info]:
        devices : list[Device.Info] = []
        for subclass in Device.__getAllSubclasses(Device):
            scanResult = subclass.scan()
            if scanResult is not None:
                devices.extend(scanResult)
        return devices

    @QtCore.pyqtSlot(JSONPacket)
    def handlePacket(self, packet : JSONPacket): 
        match packet.type:
            case JSONPacket.response:
                if packet.value == "pong":
                    self.reasureConnection()
            case JSONPacket.trigger:
                self.trigger.emit(int(packet.value))
        self._handlePacket(packet)

    def _handlePacket(self, packet : JSONPacket):
        raise NotImplementedError("_handlePacket of Device not implemented")
