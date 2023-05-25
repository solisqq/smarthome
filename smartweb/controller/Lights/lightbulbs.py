import time
from typing import Callable
import yeelight
from PyQt6 import QtWidgets
from PyQt6 import QtGui, QtCore
from controller.device import Device


class LightBulb(Device):
    def __init__(self, dev_inf : Device.Info):
        super().__init__(dev_inf)
        #self.blinkTimer = QtCore.QTimer()
        self._switchWidget = QtWidgets.QCheckBox("Enabled")
        self._switchWidget.stateChanged.connect(
            lambda x: self._on() if self._switchWidget.isChecked() else self._off())
        blabel = QtWidgets.QLabel("Brightness: ")
        ctlabel = QtWidgets.QLabel("Color temp: ")
        self._brightnessWidget = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self._brightnessWidget.sliderReleased.connect(
            lambda: self._setBrightness(self._brightnessWidget.value()))
        self._brightnessWidget.valueChanged.connect(lambda x: blabel.setText("Brightness: ("+str(x)+")"))
        self._brightnessWidget.setMaximum(100)
        self._brightnessWidget.setMinimum(0)
        self._brightnessWidget.setSingleStep(1)
        self._ctWidget = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self._ctWidget.setMaximum(5000)
        self._ctWidget.setMinimum(2999)
        self._ctWidget.setSingleStep(1)
        self._ctWidget.valueChanged.connect(lambda x: ctlabel.setText("Color temp: ("+str(x)+")"))
        self._ctWidget.sliderReleased.connect(
            lambda: self.setCt(self._ctWidget.value()))
        self.layout().addWidget(self._switchWidget)
        self.layout().addWidget(blabel)
        self.layout().addWidget(ctlabel)
        self.layout().addWidget(self._ctWidget)
        self.layout().addWidget(self._brightnessWidget)

    @QtCore.pyqtSlot(int)
    def setBrightness(self, brightnessValue):
        if brightnessValue>0 and self._brightnessWidget.value()==0: self.on()
        self._brightnessWidget.blockSignals(True)
        self._brightnessWidget.setValue(brightnessValue)
        self._brightnessWidget.blockSignals(False)
        if(brightnessValue==0): self.off()
        else: self._setBrightness(brightnessValue)

    def dimBy(self, value):
        self.setBrightness(max(0, min(100, self._brightnessWidget.value()+value)))

    @QtCore.pyqtSlot()
    def on(self):
        self._switchWidget.blockSignals(True)
        self._switchWidget.setChecked(False)
        self._switchWidget.blockSignals(False)
        self._on()

    @QtCore.pyqtSlot()
    def off(self):
        self._switchWidget.blockSignals(True)
        self._switchWidget.setChecked(False)
        self._switchWidget.blockSignals(False)
        self._off()

    def setCt(self, ct):
        self._ctWidget.blockSignals(True)
        self._ctWidget.setValue(ct)
        self._ctWidget.blockSignals(True)
        self._setCt(ct)
    
    @QtCore.pyqtSlot(int)
    def _setBrightness(self, brightnessValue): raise NotImplementedError()
    @QtCore.pyqtSlot(int)
    def _setCt(self, ct): raise NotImplementedError()
    def _on(self): raise NotImplementedError()
    def _off(self): raise NotImplementedError()
    def scan() -> list[Device.Info]: pass

class LightBulbRGB(LightBulb):
    def __init__(self, dev_inf : Device.Info):
        super().__init__(dev_inf)
        self._colorPicker = QtWidgets.QColorDialog()
        self._colorPicker.colorSelected.connect(self._setColor)
        self._colorButton = QtWidgets.QPushButton("Select color")
        self._colorButton.clicked.connect(self._colorPicker.show)
        self.layout().addWidget(self._colorButton)

    def serializeState(self) -> dict:
        return {
            "state": str(int(self._switchWidget.isChecked())),
            "color": self._colorPicker.currentColor().name(),
            "bright": str(self._brightnessWidget.value()),
            }
    
    def deserializeState(self, name : str, data : dict):
        if data["state"] == "1": self.on()
        else: self.off()
        self.setBrightness(int(data["bright"]))
        self.setColor(QtGui.QColor.fromString(data["color"]))

    @QtCore.pyqtSlot(QtGui.QColor)
    def setColor(self, color : QtGui.QColor):
        self._colorPicker.blockSignals(True)
        self._colorPicker.setCurrentColor(color)
        self._colorPicker.blockSignals(False)

    def _setColor(self, color : QtGui.QColor): raise NotImplementedError()

class YeelightLB(LightBulbRGB):
    def __init__(self, dev_inf : Device.Info):
        super().__init__(dev_inf)
        self.bulb = yeelight.Bulb(dev_inf.ip)
        self.__reconnect()
        self.hasNightMode = False
        self.__fetchToBulb(self.bulb.get_properties, self.__parseInfo)

    def __parseInfo(self, data : dict):
        self.debugDev(str(data))
        if data is not None and "power" in data.keys() and "bright" in data.keys() and "ct" in data.keys():
            if "nl_br" in data.keys() and data["nl_br"]!=None:
                self.hasNightMode = True
            self._ctWidget.blockSignals(True)
            self._brightnessWidget.blockSignals(True)
            self._colorPicker.blockSignals(True)
            self._switchWidget.blockSignals(True)
            if data["power"] == "on": self._switchWidget.setChecked(True)
            else: self._switchWidget.setChecked(False)
            if "ct" in data.keys():
                ct = int(data["ct"])
                if ct == 2999 and "rgb" in data.keys() and data["rgb"] is not None:
                    self._colorPicker.setCurrentColor(QtGui.QColor(int(data["rgb"]))) 
                else: 
                    self._ctWidget.setValue(ct)
            self._brightnessWidget.setValue(int(data["bright"]))
            self._ctWidget.blockSignals(False)
            self._brightnessWidget.blockSignals(False)
            self._colorPicker.blockSignals(False)
            self._switchWidget.blockSignals(False)

    def __reconnect(self):
        def reco():
            self.bulb._socket.close()
            self.bulb = yeelight.Bulb(self.info.ip)
        reco()

    @QtCore.pyqtSlot()
    def _on(self):
        self.__fetchToBulb(self.bulb.turn_on, None)

    @QtCore.pyqtSlot()
    def _off(self):
        self.__fetchToBulb(self.bulb.turn_off, None)

    def isOn(self) -> bool: return self._switchWidget.isChecked()

    def serializeState(self) -> dict: 
        return {
            "state": str(int(self._switchWidget.isChecked())),
            "color": self._colorPicker.currentColor().name(),
            "bright": str(self._brightnessWidget.value()),
            "ct": str(self._ctWidget.value())
            }
    
    def deserializeState(self, name : str, data : dict):
        self.debugDev(str(name)+ " "+str(data))
        if data["state"] == "0": 
            self.off()
            return
        ct = int(data["ct"])
        bright = int(data["bright"])
        color = QtGui.QColor.fromString(data["color"])
        r,g,b = (color.red(), color.green(), color.blue())
        if ct!=2999: self.__fetchToBulb(self.bulb.set_scene, None, yeelight.SceneClass.CT, ct, bright)
        else: self.__fetchToBulb(self.bulb.set_scene, None, yeelight.SceneClass.COLOR, r, g, b, bright)

    def scan() -> list[Device.Info]:
        try:
            bulbs = yeelight.discover_bulbs()
            return YeelightLB.__parseScan(bulbs)
        except: return []

    def __parseScan(scan : list[dict]):
        toRet : list[Device.Info] = []
        for bulb in scan:
            #if bulb['capabilities']['model'] != 'colorc':
            toRet.append(
                Device.Info(bulb['ip'], 
                YeelightLB,
                bulb['capabilities']['id'],
                int(bulb['port'])))
        return toRet
    
    def __fetchToBulb(self, action : Callable, handler : Callable = None, *args):
        def someAction(*arguments):
            try:
                return action(*arguments)
            except:
                self.__reconnect()
        self._safeThreadAction(someAction, handler, *args)
        
    @QtCore.pyqtSlot(QtGui.QColor)
    def _setColor(self, color : QtGui.QColor):
        self._ctWidget.setValue(2999)
        time.sleep(0.1)
        try:
            self.bulb.set_rgb(color.red(), color.green(), color.blue())
        except:
            self.debug("Failed to send command")
            self.__reconnect()

    @QtCore.pyqtSlot(int)
    def _setBrightness(self, brightnessValue):
        try:
            if self.hasNightMode:
                self.__fetchToBulb(self.bulb.set_night_mode, None, brightnessValue<10, brightnessValue)
            self.__fetchToBulb(self.bulb.set_brightness, None, brightnessValue)
        except: pass

    @QtCore.pyqtSlot(int)
    def _setCt(self, ct):
        try:
            self.__fetchToBulb(self.bulb.set_color_temp, None, ct)
        except: pass