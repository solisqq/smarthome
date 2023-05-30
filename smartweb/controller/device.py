import json
from typing import Any, Callable
from PyQt6 import QtWidgets, QtCore
from controller.Custom.Presets import PresetsController
from controller.Network.JSONProtocol import JSONPacket
import config
from controller.trigger import Trigger
from controller.util.threadutils import Threading
from .Network.database import Database

class PatternsWidget(QtWidgets.QWidget):
    addPatternSignal = QtCore.pyqtSignal(str)
    enablePattern = QtCore.pyqtSignal(str, dict)

    def exists(self, name : str):
        return name in self.__patterns.keys()

    def __init__(self, parent : QtWidgets.QWidget = None):
        super().__init__(parent)
        self.__patterns : dict[str, dict] = {}
        container = QtWidgets.QWidget()
        container.setLayout(QtWidgets.QHBoxLayout())
        container.layout().addWidget(QtWidgets.QLabel("Preset name: "))
        presetNameLineEdit = QtWidgets.QLineEdit()
        container.layout().addWidget(presetNameLineEdit)
        addBtn = QtWidgets.QPushButton("+")
        container.layout().addWidget(addBtn)
        addBtn.clicked.connect(
            lambda: self.addPatternSignal.emit(
                presetNameLineEdit.text()))
        self._comboBox = QtWidgets.QComboBox()
        self._comboBox.currentTextChanged.connect(
            lambda text:
                self.enablePattern.emit(
                    text, self.__patterns[text]["data"]))# if text != "---" else "")
        self.setLayout(QtWidgets.QVBoxLayout())
        self.layout().addWidget(self._comboBox)
        self.layout().addWidget(container)

    def set(self, name : str):
        if self.exists(name):
            self._comboBox.setCurrentText(name)

    def addPattern(self, data : dict):
        self._comboBox.blockSignals(True)
        self.__patterns.update({data["name"]: data})
        self._comboBox.addItem(data["name"])
        self._comboBox.blockSignals(False)


class BatteryWidget(QtWidgets.QWidget):
    lowBatteryDetected = QtCore.pyqtSignal(float)

    def __init__(self, batteryAlertLevel : float, parent: QtWidgets.QWidget = None):
        # batteryAlertLevel is a parameter below which this widget will
        # fire lowBatteryDetected signal once
        # 0 means it will not fire
        super().__init__(parent)
        self.setLayout(QtWidgets.QHBoxLayout())
        self.batteryWidget = QtWidgets.QProgressBar()
        self.batteryWidget.setValue(0)
        batteryLabel = QtWidgets.QLabel("Battery: ")
        self.layout().addWidget(batteryLabel)
        self.layout().addWidget(self.batteryWidget)
        self.lowBatteryAlertEmitted = False
        self.batteryAlertLevel = batteryAlertLevel
        
    @QtCore.pyqtSlot(float)
    def updateLevel(self, value : float):
        batLevel = min(max(0, value), 100)
        self.batteryWidget.setValue(int(batLevel))
        if(self.batteryAlertLevel != 0 and batLevel < self.batteryAlertLevel):
            self.lowBatteryDetected.emit(batLevel)


class Device(QtWidgets.QDialog):
    nameChanged = QtCore.pyqtSignal(str)
    disconnected = QtCore.pyqtSignal(object)
    connectionBack = QtCore.pyqtSignal(object)
    __trigger = QtCore.pyqtSignal(int, object)

    class Action:
        def __init__(self, action, handler, *args):
            self.action = action
            self.handler = handler
            self.args = args

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
        
        def instantiate(self, controller : PresetsController) -> "Device":
            device = self.devType(self)
            device.setPresetController(controller)
            return device

    def __init__(self, info : Info):
        QtWidgets.QWidget.__init__(self)
        config.Debuggable.__init__(self, info.id)
        self.info = info
        self.batteryWidget : BatteryWidget = None
        self.__thread = None
        self.debug = config.Debuggable(self.info.id)
        self._connected = True
        self._threadTasks : list[tuple] = []

        self.trigger = Trigger()
        self.__trigger.connect(self.trigger.handle)
        self.__threadQueue : list[Device.Action] = []

        self._checkConnectionTimer = QtCore.QTimer()
        self._checkConnectionTimer.timeout.connect(self.__connectionFailed)
        self._checkConnectionTimer.start(config.Device.CONNECTION_TIMEOUT_MS)
        self.setLayout(QtWidgets.QVBoxLayout())
        self.layout().addWidget(QtWidgets.QLabel("Name:"))
        self._nameLabel = QtWidgets.QLabel()
        self.layout().addWidget(self._nameLabel)
        self._patterns = PatternsWidget()
        self.layout().addWidget(self._patterns)
        self._patterns.addPatternSignal.connect(self.savePattern)
        self._patterns.enablePattern.connect(
            lambda patternName, patternData:
                self.deserializeState(patternName, patternData))
        
        btn = QtWidgets.QPushButton("DEBUG")
        self.layout().addWidget(btn)
        debugWindow = QtWidgets.QDialog(self)
        debugWindow.setLayout(QtWidgets.QVBoxLayout())
        self.__debugTextEdit = QtWidgets.QPlainTextEdit()
        self.__debugTextEdit.setMaximumBlockCount(50)
        debugWindow.setMinimumSize(500, 300)
        debugWindow.layout().addWidget(self.__debugTextEdit)
        btn.clicked.connect(debugWindow.show)

    def setPresetController(self, controller : PresetsController):
        self.__controller = controller

    def _sendToController(self, command : PresetsController.Commands, additionalArgument : int):
        self.__controller.handleCommand(command, additionalArgument)

    def debugDev(self, text : str):
        """Shows text in debug window of given device"""
        self.__debugTextEdit.appendPlainText(text)

    def addPattern(self, rawPattern : dict):
        self._patterns.addPattern(rawPattern)

    def handlePattern(self, patternName : str):
        self._patterns.set(patternName)

    def __connectionFailed(self):
        self._connected = False
        self.disconnected.emit(self)

    def _fetchThread(self, action : Callable, handler : Callable = None, *args):
        def someAction(*arguments):
            try:
                return action(*arguments)
            except: pass 
        self._safeThreadAction(someAction, handler, *args)

    @QtCore.pyqtSlot(str)
    def savePattern(self, name : str):
        if name=="---" or name == "" or self._patterns.exists(name): return
        serialized = self.serializeState()
        toExport = {"name": name, "data": json.dumps(serialized), "devName": self.getName()}
        toAdd = {"name": name, "data": serialized, "devName": self.getName()}
        Database.INSTANCE.addPattern(toExport)
        self._patterns.addPattern(toAdd)

    def serializeState(self) -> dict: return {}
    def deserializeState(self, name : str, data : dict): pass
    def _setupBattery(self, batteryWarningLevel : float):
        self.batteryWidget = BatteryWidget(batteryWarningLevel)

    @QtCore.pyqtSlot(float)
    def _updateBattery(self, battLevel : float):
        if(self.batteryWidget==None): raise NotImplementedError("Battery widget is not initialized for " + self.info.id)
        self.batteryWidget.updateLevel(battLevel)

    def reasureConnection(self):
        if(self._connected==False):
            self.connectionBack.emit(self)
        self._connected = True
        self._checkConnectionTimer.stop()
        self._checkConnectionTimer.start(config.Device.CONNECTION_TIMEOUT_MS)

    def getName(self) -> str:
        return self._nameLabel.text()

    def setName(self, newName : str): 
        self._nameLabel.setText(newName)

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

    def __handleQueue(self):
        if len(self.__threadQueue) > 0:
            action = self.__threadQueue.pop(0)
            self._safeThreadAction(action.action, action.handler, *action.args)

    def _safeThreadAction(self, action : Callable, handler : Callable, *args):
        if self.__thread == None:
            self.__thread = Threading(action, *args)
            def reset(x):
                self.__thread.wait()
                self.__thread.exit()
                self.__thread = None
            if handler is not None:
                self.__thread.dataReady.connect(handler)
            self.__thread.completed.connect(reset)
            self.__thread.completed.connect(
                lambda x:
                    QtCore.QTimer.singleShot(200, self.__handleQueue))
        else:
            self.__threadQueue.append(Device.Action(action, handler, *args))
            

