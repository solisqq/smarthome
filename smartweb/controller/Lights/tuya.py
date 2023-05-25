import binascii
import contextlib
from enum import Enum
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

        def __init__(self, data : dict):
            self.state = bool(data['20'])
            self.mode = TuyaStrip.TuyaStripInfo.Modes(data['21'])
            self.color = QtGui.QColor.fromRgb(0,0,0)#QtGui.QColor.fromString(str(data['24'].decode()))
            print(data['24'])
            h = int(data['24'][0:4], 16)
            s = int(data['24'][4:8], 16)
            v = int(data['24'][8:12], 16)
            print(h,s,v)
            self.scene = bytes.fromhex(data['25'])#str(data['25'].decode())
            self.left_time = int(data['26'])
            #print(self.color, self.scene)

    def __init__(self, dev_inf : Device.Info):
        super().__init__(dev_inf)
        self.bulb = tinytuya.BulbDevice(dev_inf.id, dev_inf.ip) #yeelight.Bulb(dev_inf.ip)
        self.bulb.set_version(float(dev_inf.port))
        self.bulb.set_socketPersistent(True)
        self.__fetchToBulb(self.bulb.status, self.__parseInfo)

    def __parseInfo(self, data : dict) -> bool:
        if data is None or "dps" not in data.keys(): return False
        data : dict = data["dps"]
        keys : list = data.keys()
        if '20' not in keys or '21' not in keys or '24' not in keys or '25' not in keys or '26' not in keys: return False
        stripInfo = TuyaStrip.TuyaStripInfo(data)
        return True

    def __reconnect(self):
        def reco():
            self.bulb.socket.close()
            self.bulb = tinytuya.BulbDevice(self.info.id, self.info.ip)
        reco()

    @QtCore.pyqtSlot()
    def _on(self):
        self.__fetchToBulb(self.bulb.turn_on, None)

    @QtCore.pyqtSlot()
    def _off(self):
        self.__fetchToBulb(self.bulb.turn_off, None)

    def serializeState(self) -> dict: 
        return {
            "state": str(int(self._switchWidget.isChecked())),
            "color": self._colorPicker.currentColor().name(),
            "bright": str(self._brightnessWidget.value()),
            "ct": str(self._ctWidget.value())
            }
    
    def deserializeState(self, name : str, data : dict):
        if data["state"] == "0": 
            self.off()
            return
        ct = int(data["ct"])
        bright = int(data["bright"])
        color = QtGui.QColor.fromString(data["color"])
        r,g,b = (color.red(), color.green(), color.blue())

    def scan() -> list[Device.Info]:
        try:
            bulbs = {}
            with open(os.devnull, "w") as f, contextlib.redirect_stdout(f):
                bulbs : dict = tinytuya.deviceScan(False, forcescan=True)
            bulbs2 : list[dict] = []
            for item in bulbs.values():
                bulbs2.append(item)
            return TuyaStrip.__parseScan(bulbs2)
        except: return []

    def __parseScan(scan : list[dict]):
        return [Device.Info(bulb['ip'], TuyaStrip, bulb['id'], bulb['version']) for bulb in scan]
    
    def __fetchToBulb(self, action : Callable, handler : Callable = None, *args):
        def someAction(*arguments):
            try:
                return action(*arguments)
            except:
                self.__reconnect()
        self._safeThreadAction(someAction, handler, *args)
        
    def _setColor(self, color : QtGui.QColor): ...
    def _setBrightness(self, brightnessValue): ...
    def _setCt(self, brightnessValue): ...

