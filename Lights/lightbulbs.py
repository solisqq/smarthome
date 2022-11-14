import yeelight
from PyQt6 import QtWidgets
from PyQt6 import QtGui, QtCore
from device import Device


class LightBulb(Device):
    def __init__(self, dev_inf : Device.Info):
        super().__init__(dev_inf)
        #self.blinkTimer = QtCore.QTimer()
        self._switchWidget = QtWidgets.QCheckBox("Enabled")
        self._switchWidget.stateChanged.connect(
            lambda x: self.on() if self._switchWidget.isChecked() else self.off())
        self.layout().addWidget(self._switchWidget)
        self.layout().addWidget(QtWidgets.QLabel("Brightness: "))
        self._brightnessWidget = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self._brightnessWidget.valueChanged.connect(self.setBrightness)
        self._brightnessWidget.setMaximum(100)
        self._brightnessWidget.setMinimum(0)
        self._brightnessWidget.setSingleStep(1)
        self.layout().addWidget(self._brightnessWidget)

    @QtCore.pyqtSlot(int)
    def setBrightness(self, brightnessValue): raise NotImplementedError()

    @QtCore.pyqtSlot()
    def on(self): raise NotImplementedError()

    @QtCore.pyqtSlot()
    def off(self): raise NotImplementedError()
    
    def scan() -> list[Device.Info]: pass

class LightBulbRGB(LightBulb):
    def __init__(self, dev_inf : Device.Info):
        super().__init__(dev_inf)
        self.colorPicker = QtWidgets.QColorDialog()
        self.colorPicker.colorSelected.connect(self.setColor)
        colorButton = QtWidgets.QPushButton("Select color")
        colorButton.clicked.connect(self.colorPicker.show)
        self.layout().addWidget(colorButton)

    @QtCore.pyqtSlot(QtGui.QColor)
    def setColor(self, color : QtGui.QColor): raise NotImplementedError()
    def scan() -> list[Device.Info]: pass

class YeelightLB(LightBulb):
    def __init__(self, dev_inf : Device.Info):
        super().__init__(dev_inf)
        self.bulb = yeelight.Bulb(dev_inf.ip)
        self._parseInfo(self.bulb.get_properties())
        
    def _parseInfo(self, properties : dict): pass

    def scan() -> list[Device.Info]:
        return YeelightLB.__parseScan(
            yeelight.discover_bulbs())
    
    def __parseScan(scan : list[dict]):
        toRet : list[Device.Info] = []
        for bulb in scan:
            if bulb['capabilities']['model'] != 'colorc':
                toRet.append(
                    Device.Info(bulb['ip'], 
                    YeelightLB,
                    bulb['capabilities']['id'],
                    int(bulb['port'])))
        return toRet

class YeelightLBRGB(LightBulbRGB):
    def __init__(self, dev_inf : Device.Info):
        super().__init__(dev_inf)
        self.bulb = yeelight.Bulb(dev_inf.ip)
        self.nameChanged.connect(self.bulb.set_name)
        self._parseInfo(self.bulb.get_properties())

    def __reconnect(self):
        self.bulb._socket.close()
        self.bulb = yeelight.Bulb(self.devInfo.ip)

    @QtCore.pyqtSlot()
    def on(self): self.bulb.turn_on()

    @QtCore.pyqtSlot()
    def off(self): self.bulb.turn_off()

    def _parseInfo(self, properties : dict):
        if isinstance(properties, dict):
            try:
                if properties['power'] == 'on': self._switchWidget.setChecked(True)
                else: self._switchWidget.setChecked(False)
                self._brightnessWidget.setValue(int(properties['bright']))
                self._nameEdit.setText(properties['name'])
            except:
                print("failed")

    def scan() -> list[Device.Info]:
        return YeelightLBRGB.__parseScan(
            yeelight.discover_bulbs())
    
    def __parseScan(scan : list[dict]):
        toRet : list[Device.Info] = []
        for bulb in scan:
            if bulb['capabilities']['model'] == 'colorc':
                toRet.append(
                    Device.Info(bulb['ip'], 
                    YeelightLBRGB,
                    bulb['capabilities']['id'],
                    int(bulb['port'])))
        return toRet
    
    @QtCore.pyqtSlot(QtGui.QColor)
    def setColor(self, color : QtGui.QColor):
        try:
            self.bulb.set_rgb(color.red(), color.green(), color.blue())
        except:
            print("TOO FAST DUDE")
            self.__reconnect()

    @QtCore.pyqtSlot(int)
    def setBrightness(self, brightnessValue):
        try:
            self.bulb.set_brightness(brightness=brightnessValue)
        except:
            print("TOO FAST DUDE")
            self.__reconnect()