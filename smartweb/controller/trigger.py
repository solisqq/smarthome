from typing import Callable
from PyQt5 import QtCore

class Action(QtCore.QObject):
    def __init__(self, handler : Callable, parent : QtCore.QObject = None):
        super().__init__(parent)
        self.__handler = handler

    def invoke(self, value = None):
        self.__handler(value)

class Trigger(QtCore.QObject):
    def __init__(self, parent : QtCore.QObject = None):
        super().__init__(parent)
        self.__triggerActions : list[tuple[int, Action]] = []

    def addAction(self, triggerId : int, action : Action):
        self.__triggerActions.append((triggerId, action))

    @QtCore.pyqtSlot(int, object)
    def handle(self, id : int, value = None):
        for triggerAction in self.__triggerActions:
            if id==triggerAction[0]:
                triggerAction[1].invoke(value)
