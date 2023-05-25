import json
import sys
# Leave it even if not used
from controller.Lights import lightbulbs, tuya
#from controller.Network.webservice import WebService
from controller.Network.JSONProtocol import JSONTalker#, JSONPacket
import config
from controller.device import Device
from controller.devicesWidget import DevicesWidget
from controller.Network.database import Database
from controller.Gate import ZigGate
from PyQt6 import QtWidgets, QtCore, QtGui
from controller.Custom.Presets import PresetsController

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, parent : QtWidgets.QWidget = None):
        super().__init__(parent)
        self.validClose = False
        self.commands = PresetsController()
        self.commands.addPreset("working", "office.working")
        self.commands.addPreset("minimal", "office.minimal")
        self.commands.addPreset("warsztat", "office.warsztat")
        #self.commands.addPreset("full", "office.full")
        self.commands.addPreset("off", "office.off")
        self.mainIcon = QtGui.QIcon("controller/misc/icon.ico")
        self.setWindowIcon(self.mainIcon)
        self.__createTrayIcon()
        
        self.server = JSONTalker(config.Controller.ADDR)
        ZigGate.zbConnection = ZigGate.ZigBeeGateConnection()
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
        self.centralWidget().layout().addWidget(self.commands)
        self.centralWidget().layout().addWidget(contentsWidget)
        
        self.devicesWidget = DevicesWidget(self.commands)
        self.commands.presetActivate.connect(self.devicesWidget.handlePresetUpdate)
        self.commands.changeBrightnessRequested.connect(self.devicesWidget.handleLightsBrightnessChange)
        self.devicesWidget.newDeviceAvailable.connect(self.__registerDevice)
        self.server.packetAvailable.connect(self.devicesWidget.handlePacket)
        contentsWidget.layout().addWidget(self.devicesWidget)
        self.devicesWidget.scanDevices()

    def __createTrayIcon(self):
        self.trayIconMenu = QtWidgets.QMenu(self)
        self.actions : list[QtGui.QAction] = []
        
        for cmd in self.commands.getPresetNames():
            self.actions.append(QtGui.QAction())
            action = self.actions[-1]
            action.setText(cmd)
            action.triggered.connect(self.handleTray)
        self.actions.append(QtGui.QAction("close"))
        self.actions[-1].triggered.connect(QtCore.QCoreApplication.quit)
        self.trayIconMenu.addActions(self.actions)
        self.trayIcon = QtWidgets.QSystemTrayIcon(self)
        self.trayIcon.setContextMenu(self.trayIconMenu)
        self.trayIcon.setToolTip("Lights controller")
        self.trayIcon.setIcon(self.mainIcon)
        self.trayIcon.messageClicked.connect(self.show)

    @QtCore.pyqtSlot()
    def handleTray(self):
        self.devicesWidget.handlePresetUpdate("office."+self.sender().text())

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        if not self.trayIcon.isVisible():
            a0.ignore()
            self.hide()
            self.trayIcon.show()

    def __registerDevice(self, dev : Device):
        patterns = self.database.getPatterns()
        for dbDev in self.database.getKnownDevices():
            if dbDev.uid == dev.info.id:
                dev.setName(dbDev.name)
                for pattern in patterns:
                    if dbDev.name == pattern.devName:
                        dev.addPattern(
                            {"name": pattern.name, 
                            "data": json.loads(pattern.data), 
                            "devName": pattern.devName})
                currentPreset = self.commands.getActivePreset()
                if currentPreset is not None:
                    dev.handlePattern(currentPreset)
                return

    def __selfCheckDevicesForChanges(self):
        self.devicesWidget.handleNamesUpdate(self.database.getKnownDevices())

app = QtWidgets.QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec()