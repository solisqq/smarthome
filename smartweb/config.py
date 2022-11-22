from typing import Any


class WebServer:
    IP = "127.0.0.1"
    PORT = 8665
    ADDR = (IP, PORT)
    NAME = 'webservice'

class Controller:
    IP = "127.0.0.1"
    PORT = 8556
    ADDR = (IP, PORT)
    NAME = 'controller'

class Database:
    PATH = "C:/Users/kamil/Documents/PlatformIO/Projects/SmartHome/smartweb/db.sqlite3"
    UPDATE_TIME_MS = 10000

class Server:
    SOCKET_TIMEOUT = 0.5

class Device:
    SCAN_MS = 20000
    CONNECTION_TIMEOUT_MS = SCAN_MS*3
    
class Debuggable:
    def __init__(self, moduleName):
        self._debug = False
        self.moduleName = moduleName

    def _setName(self, name):
        self.moduleName = name

    def enable(self):
        self._debug = True

    def debug(self, *args):
        if self._debug == True:
            print(self.moduleName, ":", *args)

    def __call__(self, *args: Any) -> Any:
        self.debug(args)
