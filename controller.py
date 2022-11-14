import sys
from typing import Callable
# Leave it even if not used
from Lights import lightbulbs
from Network.webservice import WebService
from util import threadutils
from device import Device, DevicesWidget, AvailableDevicesWidget, DeviceDialog
from PyQt6 import QtWidgets, QtCore

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, parent : QtWidgets.QWidget = None):
        super().__init__(parent)
        self.scanThread = None
        self.scanTimer = QtCore.QTimer()
        self.scanTimer.setInterval(20000)
        self.scanTimer.timeout.connect(self.__scanDevices)
        self.availableDevices : list[Device.Info] = []
        self.setCentralWidget(QtWidgets.QWidget())
        self.centralWidget().setLayout(QtWidgets.QVBoxLayout())
        menuWidget = QtWidgets.QWidget()
        menuWidget.setLayout(QtWidgets.QHBoxLayout())
        contentsWidget = QtWidgets.QWidget()
        contentsWidget.setLayout(QtWidgets.QHBoxLayout())
        self.centralWidget().layout().addWidget(menuWidget)
        self.centralWidget().layout().addWidget(contentsWidget)
        self.devicesAvailableWidget = AvailableDevicesWidget()
        self.knownDevices = DevicesWidget()
        self.devicesAvailableWidget.newDeviceSelected.connect(
            lambda devInfo: self.knownDevices.append(devInfo.instantiate()))
        self.deviceDialog = None
        def showDevDialog(device : Device):
            self.deviceDialog = DeviceDialog(device)
            self.deviceDialog.show()
        self.knownDevices.newDeviceSelected.connect(showDevDialog)    
        contentsWidget.layout().addWidget(self.devicesAvailableWidget)
        contentsWidget.layout().addWidget(self.knownDevices)
        self.rescanBtn = QtWidgets.QPushButton("Rescan")
        self.rescanBtn.clicked.connect(self.__scanDevices)
        menuWidget.layout().addWidget(self.rescanBtn)
        self.__scanDevices()
    
    def __scanDevices(self):
        if(self.scanThread is not None): return
        self.rescanBtn.setDisabled(True)
        self.scanTimer.stop()
        self.scanThread = threadutils.Threading(Device.scan)
        self.scanThread.dataReady.connect(self.__handleScanResult)
        
    def __handleScanResult(self, scanResult : list[Device.Info]):
        self.scanThread = None
        self.rescanBtn.setEnabled(True)
        self.scanTimer.start()
        self.availableDevices = scanResult
        self.devicesAvailableWidget.setSource(self.availableDevices)

        

app = QtWidgets.QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec()