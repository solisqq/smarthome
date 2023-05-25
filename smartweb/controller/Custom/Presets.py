from enum import Enum
from typing import Optional
from PyQt6 import QtWidgets, QtCore

class PresetsController(QtWidgets.QComboBox):
    
    class Commands(Enum):
        NEXT_PRESET = 0
        PREV_PRESET = 1
        LIGHT_UP = 2
        LIGHT_DOWN = 3
        TURN_OFF = 4
        TURN_ON = 5
        TOGGLE = 6
    
    presetActivate = QtCore.pyqtSignal(str)
    changeBrightnessRequested = QtCore.pyqtSignal(int)

    def __init__(self, parent = None):
        super().__init__(parent)
        self.currentIndexChanged.connect(
            lambda x: self.presetActivate.emit(
                str(self.currentData())))
    
    def addPreset(self, presetName, presetCmd):
        self.addItem(presetName, presetCmd)

    def getPresetNames(self) -> list[str]:
        return [self.itemText(i) for i in range(self.count())]

    @QtCore.pyqtSlot(Commands, int)
    def handleCommand(self, command : Commands, additionalValue = None):
        match command:
            case PresetsController.Commands.NEXT_PRESET:
                self.setCurrentIndex(
                    (self.currentIndex() - 1 - int(self.itemText((self.currentIndex() - 1) % self.count())=="off")) % self.count())
            case PresetsController.Commands.PREV_PRESET:
                self.setCurrentIndex(
                    (self.currentIndex() + 1 + int(self.itemText((self.currentIndex() + 1) % self.count())=="off")) % self.count())
            case PresetsController.Commands.TURN_ON:
                self.__turnOn()
            case PresetsController.Commands.TURN_OFF:
                self.__turnOff()
            case PresetsController.Commands.LIGHT_UP:
                if additionalValue is not None:
                    self.changeBrightnessRequested.emit(additionalValue)
            case PresetsController.Commands.LIGHT_DOWN:
                if additionalValue is not None:
                    self.changeBrightnessRequested.emit(-additionalValue)
            case PresetsController.Commands.TOGGLE:
                self.__toggle()
    
    def __turnOff(self):
        index = self.findText("off")
        if(index<0): return
        self.setCurrentIndex(index)

    def __turnOn(self):
        self.setCurrentIndex(0)

    def __toggle(self):
        if self.currentText()!="off":
            self.__turnOff()
        else:
            self.__turnOn()

    def getActivePreset(self) -> Optional[str]:
        return self.currentText()