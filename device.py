from typing import Optional
from PyQt6 import QtWidgets, QtCore

class Device(QtWidgets.QWidget):
    nameChanged = QtCore.pyqtSignal(str)

    class Info:
        def __init__(self, ip : str, devType : type, id : str, port : int, registerConnection = False):
            self.ip = ip
            self.devType = devType
            self.port = port
            self.id = id
            if registerConnection:
                pass

        def getInfo(self) -> dict:
            return {"ip": self.ip, "btype": self.devType, "id": self.id, "port": self.port}

        def __str__(self) -> str:
            return str(self.getInfo())
        
        def instantiate(self) -> "Device":
            return self.devType(self)

    def __init__(self, info : Info):
        super().__init__()
        self.devInfo = info
        self.setLayout(QtWidgets.QVBoxLayout())
        self.layout().addWidget(QtWidgets.QLabel("Name:"))
        self._nameEdit = QtWidgets.QLineEdit()
        self.layout().addWidget(self._nameEdit)
        self._nameEdit.textChanged.connect(lambda text: self.nameChanged.emit(text))

    def getName(self) -> str: return self._nameEdit.text()
    def _setName(self, newName : str) -> None: self._nameEdit.setText(newName)

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

class AvailableDevicesWidget(QtWidgets.QTableWidget):
    newDeviceSelected = QtCore.pyqtSignal(object)
    newDeviceSelected2 = QtCore.pyqtSignal(object)
    
    def __init__(self, parent : QtWidgets.QWidget = None):
        super().__init__(parent)
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self._devices : list[Device] = []
        self.setMinimumWidth(420)
        self.setColumnCount(4)
        self.cellClicked.connect(lambda row, column: self.newDeviceSelected.emit(self.getSelectedDevice()))
        self.cellDoubleClicked.connect(lambda row, column: self.newDeviceSelected2.emit(self.getSelectedDevice()))

    def setSource(self, devices : list[Device.Info]) -> None:
        self.setRowCount(len(devices))
        self.clear()
        self._devices = devices
        for i, device in enumerate(devices):
            self.setItem(i, 0, QtWidgets.QTableWidgetItem(str(device.devType.__name__)))
            self.setItem(i, 1, QtWidgets.QTableWidgetItem(device.ip))
            self.setItem(i, 2, QtWidgets.QTableWidgetItem(device.id))
            self.setItem(i, 3, QtWidgets.QTableWidgetItem(str(device.port)))

    def getSelectedDevice(self) -> Optional[Device.Info]:
        if len(self.selectedIndexes())>0:
            return self._devices[self.selectedIndexes()[0].row()]
        else: return None


class DevicesWidget(AvailableDevicesWidget):

    def __init__(self, parent : QtWidgets.QWidget = None):
        super().__init__(parent)
        self.setColumnCount(5)
        self.setMinimumWidth(520)

    def setSource(self, devices : list[Device]):
        self.clear()
        self.setRowCount(len(devices))
        self._devices = devices
        for i, device in enumerate(devices):
            self.setItem(i, 0, QtWidgets.QTableWidgetItem(device.name))
            self.setItem(i, 1, QtWidgets.QTableWidgetItem(str(device.devType.__name__)))
            self.setItem(i, 2, QtWidgets.QTableWidgetItem(device.devInfo.ip))
            self.setItem(i, 3, QtWidgets.QTableWidgetItem(device.devInfo.id))
            self.setItem(i, 4, QtWidgets.QTableWidgetItem(str(device.devInfo.port)))

    def getSelectedDevice(self) -> Optional[Device]:
        if len(self.selectedIndexes())>0:
            return self._devices[self.selectedIndexes()[0].row()]
        else: return None

    def append(self, device : Device):
        id = len(self._devices)
        self._devices.append(device)
        self.insertRow(id)
        device.nameChanged.connect(lambda name: self.setItem(id, 0, QtWidgets.QTableWidgetItem(name)))
        self.setItem(id, 0, QtWidgets.QTableWidgetItem(device.getName()))
        self.setItem(id, 1, QtWidgets.QTableWidgetItem(str(device.devInfo.devType.__name__)))
        self.setItem(id, 2, QtWidgets.QTableWidgetItem(device.devInfo.ip))
        self.setItem(id, 3, QtWidgets.QTableWidgetItem(device.devInfo.id))
        self.setItem(id, 4, QtWidgets.QTableWidgetItem(str(device.devInfo.port)))


class DeviceDialog(QtWidgets.QDialog):
    def __init__(self, device : Device, parent : QtWidgets.QWidget = None):
        super().__init__(parent)
        self.setLayout(QtWidgets.QVBoxLayout())
        self.infoWidget = QtWidgets.QLabel(device.devInfo.devType.__name__+"   "+device.devInfo.id)
        self.layout().addWidget(self.infoWidget)
        self.layout().addWidget(device)

