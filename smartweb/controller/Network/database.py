import sqlite3
from PyQt6 import QtCore
import config

class Database(QtCore.QObject):

    # class BasicOps:                
    #     def getAll(tableName : str, connection : sqlite3.Connection) -> list:
    #         cur = connection.cursor()
    #         cur.execute("SELECT * from smartmanage_"+tableName)
    #         return cur.fetchall()

        #def add(tableName : str, connection : sqlite3.Connection):
    class BasicOps:
        def getAll(tableName, connection : sqlite3.Connection):
            if connection is None: return []
            cur = connection.cursor()
            cur.execute("SELECT * from smartmanage_"+tableName)
            return cur.fetchall()

        #def add(tableName : str, connection : sqlite3.Connection):

    class Models:
        class Model:
            def getName()->str:
                raise NotImplementedError("Not implemented getName Model in db.")
            def serialize(self) ->str:
                raise NotImplementedError("Not implemented serialize Model in db.")
            def getAll(data : list) -> list["Database.Models.Model"]:
                raise NotImplementedError("Not implemented deserialize Model in db.")

        class KnownDevices(Model):
            items : list["Database.Models.KnownDevices"] = []

            def __init__(self, name, uid):
                self.name : str = name
                self.uid : str = uid

            def getAll(connection : sqlite3.Connection) -> list["Database.Models.KnownDevices"]:
                data = Database.BasicOps.getAll("knowndevices", connection)
                toRet : list["Database.Models.KnownDevices"] = []
                for kd in data:
                    toRet.append(Database.Models.KnownDevices(kd[1],kd[2]))
                Database.Models.KnownDevices.items = toRet
                return Database.Models.KnownDevices.items

        class Patterns(Model):
            items : list["Database.Models.Patterns"] = []

            def __init__(self, name : str, data : str, deviceType : str):
                self.name : str = name
                self.data : str = data
                self.deviceType : str = deviceType

            def getAll(connection : sqlite3.Connection) -> list["Database.Models.Patterns"]:
                data = Database.BasicOps.getAll("patterns", connection)
                toRet : list["Database.Models.Patterns"] = []
                for kd in data:
                    toRet.append(Database.Models.Patterns(kd[1],kd[2],kd[3]))
                Database.Models.Patterns.items = toRet
                return Database.Models.Patterns.items

    def __init__(self, dbfile : str):
        QtCore.QObject.__init__(self)
        config.Debuggable.__init__(self, "Database:")
        self.dbfilePath = dbfile
        self.__connection : sqlite3.Connection = None
        self.debug = config.Debuggable("Database")
        #self.debug.enable()
        try:
            self.__connection = sqlite3.connect(dbfile)
            self.__update()
        except:
            self.debug("Unable to connect to database.")

    def getKnownDevices(self) -> list["Database.Models.KnownDevices"]:
        return Database.Models.KnownDevices.getAll(self.__connection)

    def getPatterns(self) -> list["Database.Models.Patterns"]:
        return Database.Models.Patterns.getAll(self.__connection)

    def __update(self):
        self.debug(self.getKnownDevices())
        self.debug(self.getPatterns())

    def isConnected(self) -> bool:
        return True if self.__connection is not None else False