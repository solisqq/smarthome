from device import Device
import requests
from util import threadutils
from Network.server import Server, SmartMessage
# class ControllDevice(Device):
#     class Trigger(Qt):
#     def __init__(self, devInfo : Device.Info):
#         super().__init__(devInfo)
#         self._triggers = []

class WebService(Device):

    def __init__(self, devInfo : Device.Info):
        super().__init__(devInfo)
        Server.get().send(self, {"test":"test"}, self.handleMsg)

    def scan():
        response = Server.independentSend(SmartMessage.request(
            'controller',
            'http://127.0.0.1:8000/requests',
            {'question': 'isAvailable'}
        ))
        if response is not None and response['isAvailable'] == 'True':
            return [Device.Info("http://127.0.0.1:8000/requests", WebService, "MainWebService", 8000)]
        return []

    def handleMsg(self, msg):
        print(msg)