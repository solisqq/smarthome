from PyQt6 import QtCore
from typing import Callable

class Threading(QtCore.QThread):
    dataReady = QtCore.pyqtSignal(object)

    def __init__(self, func : Callable, *args):
        super().__init__()
        self.func = func
        self.args = args
        self.start()
        
    @QtCore.pyqtSlot()
    def run(self):
        self.dataReady.emit(self.func(*self.args))

class InifinityThread(QtCore.QThread):
    def __init__(self, func : Callable, *args):
        super().__init__()
        self.func = func
        self.args = args
        self.start()
        
    @QtCore.pyqtSlot()
    def run(self):
        while(True):
            self.func(*self.args)