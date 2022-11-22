import sys
# Leave it even if not used
from controller.Lights import lightbulbs
from controller.Network.webservice import WebService
from controller.Network.JSONProtocol import JSONTalker, JSONPacket
import config
from controller.device import Device
from controller.devicesWidget import DevicesWidget
from controller.Network.database import Database
from PyQt6 import QtWidgets, QtCore

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, parent : QtWidgets.QWidget = None):
        super().__init__(parent)
        self.server = JSONTalker(config.Controller.ADDR)
        self.setCentralWidget(QtWidgets.QWidget())
        self.centralWidget().setLayout(QtWidgets.QVBoxLayout())

        self.database = Database(config.Database.PATH)

        self.__updateTimer = QtCore.QTimer()
        self.__updateTimer.timeout.connect(self.__selfCheckDevicesForChanges)
        self.__updateTimer.start(config.Database.UPDATE_TIME_MS)

        menuWidget = QtWidgets.QWidget()
        menuWidget.setLayout(QtWidgets.QHBoxLayout())

        contentsWidget = QtWidgets.QWidget()
        contentsWidget.setLayout(QtWidgets.QHBoxLayout())

        self.centralWidget().layout().addWidget(menuWidget)
        self.centralWidget().layout().addWidget(contentsWidget)
        
        self.devicesWidget = DevicesWidget()
        self.devicesWidget.newDeviceAvailable.connect(self.__registerDevice)
        self.server.packetAvailable.connect(self.devicesWidget.handlePacket)
        contentsWidget.layout().addWidget(self.devicesWidget)

        self.devicesWidget.scanDevices()

    def __registerDevice(self, dev : Device):
        for dbDev in self.database.getKnownDevices():
            if dbDev.uid == dev.info.id:
                dev.setName(dbDev.name)
                return

    def __selfCheckDevicesForChanges(self):
        self.devicesWidget.handleNamesUpdate(self.database.getKnownDevices())

        

app = QtWidgets.QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec()