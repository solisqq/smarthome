import binascii
import contextlib
from enum import Enum
import json
import math
import os
import struct
import tinytuya
from typing import Callable
import yeelight
from PyQt6 import QtWidgets
from PyQt6 import QtGui, QtCore
from controller.device import Device
from controller.Lights.lightbulbs import LightBulbRGB

"""
#### Version 3.3 - Light Type (RGB)
| DP ID        | Function Point | Type        | Range       | Units |
| ------------- | ------------- | ------------- | ------------- |------------- |
| 20|Switch|bool|True/False||
| 21|Mode|enum|white,colour,scene,music||
| 22|Bright|integer|10-1000*||
| 23|Color Temp|integer|0-1000||
| 24|Color|hexstring|h:0-360,s:0-1000,v:0-1000|hsv|
| 25|Scene|string|n/a||
| 26|Left time|integer|0-86400|s|
| 27|Music|string|n/a||
| 28|Debugger|string|n/a||
| 29|Debug|string|n/a||
"""

class TuyaStrip(LightBulbRGB):
    class TuyaStripInfo:
        class Modes(Enum):
            WHITE = 'white'
            COLOUR = 'colour'
            SCENE = 'scene'
            MUSIC = 'music'
        
        class DpsIds(Enum):
            STATE = '20'
            BRIGHT = '22'
            MODE = '21'
            COLOR = '24'
            SCENE = '25'
            LEFT_TIME = '26'

        def __init__(self, data : dict):
            self.state = bool(data[str(TuyaStrip.TuyaStripInfo.DpsIds.STATE.value)])
            self.mode = TuyaStrip.TuyaStripInfo.Modes(data[str(TuyaStrip.TuyaStripInfo.DpsIds.MODE.value)])
            self.color = QtGui.QColor.fromHsv(
                int(data[TuyaStrip.TuyaStripInfo.DpsIds.COLOR.value][0:4], 16),
                int(int(data[TuyaStrip.TuyaStripInfo.DpsIds.COLOR.value][4:8], 16)/3.92),
                int(int(data[TuyaStrip.TuyaStripInfo.DpsIds.COLOR.value][8:12], 16)/3.92))
            self.scene = data[TuyaStrip.TuyaStripInfo.DpsIds.SCENE.value]
            self.left_time = int(data[TuyaStrip.TuyaStripInfo.DpsIds.LEFT_TIME.value])

    def __init__(self, dev_inf : Device.Info):
        super().__init__(dev_inf)
        self.bulb = tinytuya.BulbDevice(dev_inf.id, dev_inf.ip) #yeelight.Bulb(dev_inf.ip)
        self.bulb.set_version(float(dev_inf.port))
        self.bulb.set_socketPersistent(True)
        self._fetchThread(self.bulb.status, self.__parseInfo)

    def __parseInfo(self, data : dict) -> bool:
        if data is None or "dps" not in data.keys(): return False
        data : dict = data["dps"]
        keys : list = data.keys()
        if '20' not in keys or '21' not in keys or '24' not in keys or '25' not in keys or '26' not in keys: return False
        stripInfo = TuyaStrip.TuyaStripInfo(data)
        self.debugDev(str(data))

        self._ctWidget.blockSignals(True)
        self._brightnessWidget.blockSignals(True)
        self._colorPicker.blockSignals(True)
        self._switchWidget.blockSignals(True)
        self._switchWidget.setChecked(stripInfo.state)
        self._colorPicker.setCurrentColor(stripInfo.color) 
        self._ctWidget.setValue(5000)
        self._brightnessWidget.setValue(int(stripInfo.color.value()/2.55))
        self._ctWidget.blockSignals(False)
        self._brightnessWidget.blockSignals(False)
        self._colorPicker.blockSignals(False)
        self._switchWidget.blockSignals(False)
        return True

    @QtCore.pyqtSlot()
    def _on(self):
        self._setBrightness(50)

    @QtCore.pyqtSlot()
    def _off(self):
        self._setBrightness(0)
    
    def qColorToHexString(color : QtGui.QColor):
        # Convert the integers to hexadecimal strings
        if color.hsvHue()<0: r_hex = "0000"
        else: r_hex = format(color.hsvHue(), '04x')
        g_hex = format(color.hsvSaturation(), '04x')
        b_hex = format(color.value(), '04x')

        # Concatenate the hexadecimal strings
        hex_string = r_hex + g_hex + b_hex

        return hex_string

    def translateToRange(value, leftMin, leftMax, rightMin, rightMax):
        # Figure out how 'wide' each range is
        leftSpan = leftMax - leftMin
        rightSpan = rightMax - rightMin

        # Convert the left range into a 0-1 range (float)
        valueScaled = float(value - leftMin) / float(leftSpan)

        # Convert the 0-1 range into a value in the right range.
        return rightMin + (valueScaled * rightSpan)

    def deserializeState(self, name : str, data : dict):
        state =  True if "1" == data["state"] or 1 == data["state"] else False
        ct = int(data["ct"])
        bright = int(data["bright"])
        color = QtGui.QColor.fromString(data["color"])
        if not state:
            self.off()
            return
        self._fetchThread(self.bulb.set_hsv, None, abs(color.hsvHueF()), color.hsvSaturationF(), bright/100.0, True)

    def scan() -> list[Device.Info]:
        try:
            bulbs = {}
            with open(os.devnull, "w") as f, contextlib.redirect_stdout(f):
                bulbs : dict = tinytuya.deviceScan(False, forcescan=True)
            bulbs2 : list[dict] = []
            for item in bulbs.values():
                bulbs2.append(item)
            return [Device.Info(bulb['ip'], TuyaStrip, bulb['id'], bulb['version']) for bulb in bulbs2]
        except: return []

    def _setColor(self, color : QtGui.QColor):
        self._fetchThread(
            self.bulb.set_hsv, None, abs(color.hsvHueF()), color.hsvSaturationF(), self._brightnessWidget.value()/100.0, True)

    def _setBrightness(self, brightnessValue):
        self._fetchThread(
            self.bulb.set_hsv, None, 
            abs(self._colorPicker.currentColor().hsvHueF()), 
            self._colorPicker.currentColor().hsvSaturationF(), 
            brightnessValue/100.0, True)

    def _setCt(self, ct):
        ctColor = TuyaStrip.colorTempToRGB(ct)
        print(ctColor.red(), ctColor.green(), ctColor.blue())
        self._fetchThread(
            self.bulb.set_hsv, None, 
            abs(ctColor.hsvHueF()), 
            ctColor.hsvSaturationF(), 
            self._brightnessWidget.value()/100.0)
        
    def colorTempToRGB(ct : int) -> QtGui.QColor:
        temp = ct/100
        if temp <= 66: red = 255
        else: 
            red = temp - 60
            red = 329.698727446 * math.pow(red, -0.1332047592)
            if red < 0: red = 0
            elif red > 255: red = 255
    
        if temp <= 66:
            green = temp
            green = 99.4708025861 * math.log(green) - 161.1195681661
            if green < 0: green = 0
            if green > 255: green = 255
        else:
            green = temp - 60
            green = 288.1221695283 * math.pow(green, -0.0755148492)
            if green < 0: green = 0
            if green > 255: green = 255

        if temp >= 66:
            blue = 255
        else:
            if temp <= 19:
                blue = 0
            else:
                blue = temp - 10
                blue = 138.5177312231 * math.log(blue) - 305.0447927307
                if blue < 0: blue = 0
                if blue > 255: blue = 255
        return QtGui.QColor.fromRgb(int(red), int(green), int(blue))

