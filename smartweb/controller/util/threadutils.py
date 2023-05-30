from PyQt5 import QtCore
from typing import Callable

class Threading(QtCore.QThread):
    dataReady = QtCore.pyqtSignal(object)
    completed = QtCore.pyqtSignal(int)

    def __init__(self, func : Callable, *args):
        super().__init__()
        self.func = func
        self.args = args
        self.start()

    # USE TO DEBUG THREADING  
    # def __del__(self):
    #     print("deleting", self.func.__name__, self.func)

    @QtCore.pyqtSlot() 
    def run(self):
        try:
            result = self.func(*self.args)
            self.dataReady.emit(result)
            self.completed.emit(0)
        except:
            self.completed.emit(1)
            print("FAILED THDUTILS: "+self.func.__name__)
        self.msleep(500)

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