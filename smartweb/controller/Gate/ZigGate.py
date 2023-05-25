import json
import re
from controller.device import Device
from PyQt6 import QtWidgets, QtCore
import subprocess
from controller.Custom.Presets import PresetsController

ZIGBEE2MQTT_DIR = "C:/Users/kamil/Documents/PlatformIO/Projects/SmartHome/zigbee2mqtt/"
NPM_DIR = "C:/Program Files/nodejs/npm.cmd"


class ZigBeeGateConnection(QtCore.QThread):
    MQTTBROKER = '127.0.0.1'
    PORT = 1883
    dataAvailable = QtCore.pyqtSignal(str, dict)

    class ZigBeeDeviceInfo:
        def __init__(self, id : str):
            self.id = id
            self.data = {}
            self.lastUpdate = QtCore.QDateTime.currentDateTime()

        def update(self, data : dict):
            self.lastUpdate = QtCore.QDateTime.currentDateTime()
            self.data = data

    class ZigBeeDeviceInterface:
        def handleMsgReceived(self, msg : dict):
            raise NotImplementedError("ZigBeeDeviceInterface handleMsgReceived not implemented ")

    def __init__(self):
        super().__init__()
        self.__process = subprocess.Popen(
            [NPM_DIR, 'start'], 
            cwd=ZIGBEE2MQTT_DIR, 
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        self.__devicesInfo : list[ZigBeeGateConnection.ZigBeeDeviceInfo] = []
        self.__devices : list[ZigBeeGateConnection.ZigBeeDeviceInterface] = []
        self.start()

    def parseMQTT(msg : str):
        # Extracting information using regular expressions
        pattern = r'^\w+:(\w+)\s+(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2}:\d{2}).+topic\s+\'(.+)\',\s+payload\s+\'(.+)\'.+$'
        matches = re.match(pattern, msg)
        if matches is None: return None

        # Returning the dictionary
        try:
            return {
                "type": matches.group(1),
                "date": matches.group(2),
                "time": matches.group(3),
                "topic": matches.group(4),
                "payload": json.loads(matches.group(5))}
            
        except: return None


    @QtCore.pyqtSlot()
    def run(self):
        for line in iter(self.__process.stdout.readline,''):
            line = str(line.decode())
            if("MQTT publish" in line):
                mqttMsg = ZigBeeGateConnection.parseMQTT(line)
                if mqttMsg==None: continue
                inAvailable = False
                for dev in self.__devicesInfo:
                    if dev.id == mqttMsg["topic"]: inAvailable = True
                if not inAvailable:
                    self.__devicesInfo.append(ZigBeeGateConnection.ZigBeeDeviceInfo(mqttMsg["topic"]))
                    self.__devicesInfo[-1].update(mqttMsg["payload"])
                self.dataAvailable.emit(mqttMsg["topic"], mqttMsg["payload"])
    
    def isIdAvailable(self, devId : str) -> bool:
        for dev in self.__devicesInfo:
            if dev.id == devId: return True
        return False
    
    def subscribe(self, device : Device) -> ZigBeeDeviceInfo:
        for dev in self.__devicesInfo:
            if dev.id == device.info.id:
                device.debugDev(str(device.info.id) + "  " + str(dev.id) + " added")
                zbConnection.addDevice(device)
                return dev
        return None
    
    def addDevice(self, device : ZigBeeDeviceInterface):
        self.__devices.append(device)
        self.dataAvailable.connect(
            lambda emitDevId, data: \
                device.handleMsgReceived(data) if device.info.id == emitDevId else print(id, emitDevId))


zbConnection : ZigBeeGateConnection = None

# class NativeController:
#     def __init__(self, controller : PresetsController):
#         self.controller = controller        

class ZigBeeKnob(Device, ZigBeeGateConnection.ZigBeeDeviceInterface): #NativeController):
    DEVICES_ID = ["zigbee2mqtt/0x540f57fffe37df65"]

    def __init__(self, dev_inf : Device.Info):
        super().__init__(dev_inf)
        zbConnection.subscribe(self)
        self.batteryWidget = QtWidgets.QProgressBar()
        self._setupBattery(30)

    def handleMsgReceived(self, msg : dict):
        value = None
        if 'action_step_size' in msg.keys():
            value = msg['action_step_size']
        if "battery" in msg.keys():
            self._updateBattery(float(msg["battery"]))
        if "action" in msg.keys():
            match msg["action"]:
                #case "double" | "": self._sendToController(PresetsController.Commands.TOGGLE,0)
                case "double" | "toggle": 
                    self._sendToController(PresetsController.Commands.TOGGLE,0)
                case "single": 
                    self._sendToController(PresetsController.Commands.NEXT_PRESET,0)
                case "brightness_step_up":
                    if value is not None and value>30:
                        self._sendToController(PresetsController.Commands.NEXT_PRESET, 0)
                case "brightness_step_down":
                    if value is not None and value>30:
                        self._sendToController(PresetsController.Commands.PREV_PRESET, 0)
                case "rotate_right" | "color_temperature_step_down":
                    self._sendToController(
                        PresetsController.Commands.LIGHT_UP, value if value is not None else 10)
                case "rotate_left" | "color_temperature_step_up": 
                    self._sendToController(
                        PresetsController.Commands.LIGHT_DOWN, value if value is not None else 10)
                case "color_temperature_step_down":
                    if value is not None and value>50:
                        self._sendToController(
                            PresetsController.Commands.LIGHT_UP, value/3 if value is not None else 10)
                case "color_temperature_step_up":
                    if value is not None and value>50:
                        self._sendToController(
                            PresetsController.Commands.LIGHT_DOWN, value/3 if value is not None else 10)
        self.debugDev(str(msg))

    def scan() -> list[Device.Info]:
        for devid in ZigBeeKnob.DEVICES_ID:    
            if zbConnection.isIdAvailable(devid):
                return [Device.Info("127.0.0.1", ZigBeeKnob, devid, 1883)]
        return []
