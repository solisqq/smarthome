from typing import Optional
from PyQt6 import QtWidgets, QtCore
from controller.Custom.Presets import PresetsController
from controller.Lights.lightbulbs import LightBulb
from controller.Network.database import Database
from controller.util import threadutils
from controller.Network.JSONProtocol import JSONPacket
from controller.device import Device
import config

class DevicesWidget(QtWidgets.QWidget):
    newDeviceSelected = QtCore.pyqtSignal(object)
    newDeviceSelected2 = QtCore.pyqtSignal(object)
    newDeviceAvailable = QtCore.pyqtSignal(Device)
    
    def __init__(self, presetsController : PresetsController, parent : QtWidgets.QWidget = None):
        super().__init__(parent)
        self.setLayout(QtWidgets.QVBoxLayout())
        self.presetsController = presetsController
        self.tableWidget = QtWidgets.QTableWidget()
        self.tableWidget.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.tableWidget.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self.tableWidget.setMinimumWidth(520)
        self.tableWidget.setColumnCount(5)
        self.tableWidget.cellClicked.connect(lambda row, column: self.newDeviceSelected.emit(self.getSelectedDevice()))
        self.tableWidget.cellDoubleClicked.connect(lambda row, column: self.newDeviceSelected2.emit(self.getSelectedDevice()))
        self.layout().addWidget(self.tableWidget)

        self.rescanBtn = QtWidgets.QPushButton("Rescan")
        self.rescanBtn.clicked.connect(self.scanDevices)
        self.layout().addWidget(self.rescanBtn)

        self.scanThread = None
        self.scanTimer = QtCore.QTimer()
        self.scanTimer.setInterval(config.Device.SCAN_MS)
        self.scanTimer.timeout.connect(self.scanDevices)

        self.deviceDialog = None
        self.newDeviceSelected.connect(self.__showDevDialog) 

        self._devices : list[Device] = []

    def __showDevDialog(self, device : Device):
        device.show()

    @QtCore.pyqtSlot(JSONPacket)
    def handlePacket(self, packet : JSONPacket):
        for dev in self._devices:
            if dev.info.id == packet.srcName:
                dev.handlePacket(packet)

    def getSelectedDevice(self) -> Optional[Device]:
        if len(self.tableWidget.selectedIndexes())>0:
            return self._devices[self.tableWidget.selectedIndexes()[0].row()]
        else: return None

    def append(self, device : Device):
        self.newDeviceAvailable.emit(device)
        id = len(self._devices)
        self._devices.append(device)
        self.tableWidget.insertRow(id)
        device.nameChanged.connect(lambda name: self.tableWidget.setItem(id, 0, QtWidgets.QTableWidgetItem(name)))
        self.tableWidget.setItem(id, 0, QtWidgets.QTableWidgetItem(device.getName()))
        self.tableWidget.setItem(id, 1, QtWidgets.QTableWidgetItem(str(device.info.devType.__name__)))
        self.tableWidget.setItem(id, 2, QtWidgets.QTableWidgetItem(device.info.ip))
        self.tableWidget.setItem(id, 3, QtWidgets.QTableWidgetItem(device.info.id))
        self.tableWidget.setItem(id, 4, QtWidgets.QTableWidgetItem(str(device.info.port)))

    def scanDevices(self):
        if(self.scanThread is not None): return
        self.rescanBtn.setDisabled(True)
        self.scanTimer.stop()
        self.scanThread = threadutils.Threading(Device.scan)
        self.scanThread.dataReady.connect(self.__handleScanResult)

    def __handleScanResult(self, scanResult : list[Device.Info]):
        self.scanThread = None
        self.rescanBtn.setEnabled(True)
        self.scanTimer.start()
        for devInfo in scanResult:
            isRegistered=False
            for device in self._devices:
                if devInfo.id == device.info.id:
                    device.reasureConnection()
                    isRegistered = True
            if not isRegistered:
                self.append(devInfo.instantiate(self.presetsController))

    def handlePresetUpdate(self, presetName : str):
        for dev in self._devices:
            dev.handlePattern(presetName)

    @QtCore.pyqtSlot(int)
    def handleLightsBrightnessChange(self, value : int): 
        for dev in self._devices:
            if(isinstance(dev, LightBulb)):
                dev.dimBy(value)

    def handleNamesUpdate(self, knownDevices : list[Database.Models.KnownDevices]):
        for dev in self._devices:
            for kdev in knownDevices:
                if dev.info.id == kdev.uid:
                    if dev.getName() != kdev.name:
                        dev.setName(kdev.name)



# class DeviceDialog(QtWidgets.QDialog):
#     def __init__(self, device : Device, parent : QtWidgets.QWidget = None):
#         super().__init__(parent)
#         self.setLayout(QtWidgets.QVBoxLayout())
#         self.infoWidget = QtWidgets.QLabel(device.info.devType.__name__+"   "+device.info.id)
#         self.layout().addWidget(self.infoWidget)
#         self.layout().addWidget(device)
    
#     def __del__(self):
#         self.close()