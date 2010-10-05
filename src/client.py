#!/usr/bin/env python
#coding=utf8

import time
import xml.sax
import device
from common import Actionlog, AssignmentXmlHandler, Connector
import ConfigParser
import xmltemplate

class State:
    """
    Ist eine Informationssammlung, was der Client gerade über sich weiß.
    Wie weit gefahren?
    Wie weit gedreht?
    Ist der Saugkopft unten?
    Was sagen die Sensoren?
    """

    def __init__(self, cb_process):
        self.actionlog = Actionlog()
        self.dict = {}
        self.cb_anyAction = cb_process
        self.devices = {}

    def __del__(self):
        self.quit()

    def addDevice(self, name, default=0.0):
        """ Hinzufügen eines Devices """
        if self.devices.has_key(name):
            dev = self.devices.pop(name)
            if dev:
                dev.close()
        self.devices[name] = device.Device(name, lambda data: self.preUpdate(name, data))
        self.devices[name].write("reset=1")

    def clearActionlog(self):
        self.actionlog.clear()

    def getValue(self, key):
        """ Gibt den value zu key """
        value = None
        if self.dict.has_key(key):
            value = self.dict[key]
        return value

    def getActionlogXml(self):
        return self.actionlog.toXml()

    def quit(self):
        if self.devices:
            for dev in self.devices.values():
                dev.close()
            self.devices = None
        if self.actionlog:
            self.actionlog.quit()
            self.actionlog = None

    def preUpdate(self, name, value, process=True):
        """ die Informationen von Device in brauchbare Key=Value umwandeln """
        # name = "engine"
        # value = "turn=left"

        value = value.split("=")
        if len(value) > 1:
            name += ":" + value[0]
            value = value[1]

            if value == "down":
                value = 1.0
            elif value == "right":
                value = 1.0
            elif value == "left":
                value = -1.0
            else:
                try:
                    value = float(value)
                except ValueError:
                    value = 0.0

            self.update(name, value, process)
        return 0

    def update(self, key, value, process=True):
        """ Erstellt/Aktualisiert einen Wert """
        self.dict[key] = value
        self.actionlog.update(key, value)
        if process and self.cb_anyAction:
            self.cb_anyAction()

class Client:
    """
    Die Zusammenfassung aller Instrumente und Main-Klasse.
    """

    def __init__(self):
        self.process_active = False
        self.assignment = None            # Letztes ausgeführtes Assignment
        self.assignments = []
        self.stateholder = None
        self.connection = None

    def __del__(self):
        if self.connection:
            self.connection.disconnect(True)

    def getNextAssignments(self):
        """ holt neue Aufgaben vom Server """
        self.assignment    = None
        self.assignments   = []
        data = self.connection.read(flushData=True)
        if data:
            print data
            try:
                xmltemplate.readTransmissionData("<document>" + data + "</document>") #its "junk" without <document/>
            except Exception as e:
                print "no valid xml tki? " + e.message
            try:
                xmltemplate.processTemplates(AssignmentXmlHandler(self))
            except:
                print "no valid xml template?"
        return 0

    def initialize (self):
        """ Lädt Konfiguration und initialisiert Stateholder, Connection """
        self.stateholder = State(self.process)

        config = ConfigParser.RawConfigParser()
        try:
            try:
                config.read("/etc/marvin.conf")

                self.stateholder.update("self:Ident", config.get("client", "ident"), process=False)
                self.stateholder.update("self:Stamp", str(time.time()), process=False)
                self.stateholder.update("self:Tolerance", config.getfloat("client", "tolerance"), process=False)
                self.stateholder.update("self:Radius", config.getfloat("client", "radius"), process=False)

                ServerIP = config.get("client", "ServerIP")
                ServerPort = config.getint("client", "ServerPort")

                for section in ("SensorDevices", "EngineDevices", "HeadDevices"):
                    devlist = config.get("client", section)
                    for devname in devlist.split(","):
                        if config.has_option(devname, "dimension"):
                            self.stateholder.update(devname + ":dimension", \
                                                    config.get(devname, "dimension"), \
                                                    process=False)
                        if config.has_option(devname, "orientation"):
                            self.stateholder.update(devname + ":orientation", \
                                                    config.get(devname, "orientation"), \
                                                    process=False)
                        if config.has_option(devname, "output"):
                            for output in config.get(devname, "output").split(";"):
                                self.stateholder.update(devname + ":" + output.split("=")[0], \
                                                        float(output.split("=")[1]), \
                                                        process=False)
                        self.stateholder.addDevice(devname)
            except Exception, e:
                print "ERROR: Configuration missing or incomplete."
                print e.message
                return 0

            try:
                self.connection = Connector(ServerIP, ServerPort)
                self.connection.setCbDisconnect(self.networkDisconnection)
            except Exception, e:
                print "ERROR: Connection failed."
                print e.message
                return 0

            return 1
        finally:
            config = None

    def runNextAssignment(self):
        """ aktiviert das nächste Assignment """
        activated = False
        self.process_active = True

        if self.assignment:
            activated = self.assignment.active

        if not activated:
            for a in self.assignments:
                if self.assignment == None or a.id > self.assignment.id:
                    self.assignment = a
                    self.assignment.start(self.stateholder)
                    activated = True
                    break
        self.process_active = False
        return activated

    def sendActionlog(self):
        """ unterrichtet den Server """
        xml = self.stateholder.getActionlogXml()
        if xml:
            self.connection.write(xml)
        self.stateholder.clearActionlog()
        return 1

    def run(self):
        """ Main loop """
        if not self.initialize():
            return 0

        active = 0
        while 1:
            try:
                time.sleep(1)
                # erstes/nächstes Assignment ausführen
                active = self.runNextAssignment()
                # sekündliche Prüfung
                if active:
                    self.process()
                # wenn nichts mehr zu tun ist
                # Verbindugn zum Server aufbauen,
                # Bericht an den Server senden und neue Aufgaben holen
                else:
                    self.sendActionlog()
                    self.getNextAssignments()
            except KeyboardInterrupt:
                break

        # Serververbindung trennen
        if self.connection:
            self.connection.disconnect(True)

        self.quit()

    def process(self):
        if (not self.process_active) and self.assignment:
            self.process_active = True
            self.stateholder.update("running", time.time() - self.assignment.starttime, process=False)
            self.assignment.process(self.stateholder)
            self.process_active = False

    def quit(self):
        self.process_active = False
        self.assignment = None
        for a in self.assignments:
            a.quit()
        self.assignments = []

        self.connection.disconnect(True)
        self.connection = None

        self.stateholder.quit()
        self.stateholder = None

    def networkDisconnection(self, connection):
        print "network disconnect"
        self.quit()

if __name__ == '__main__':
    print "init client"
    client = Client()
    print "run client"
    client.run()
    print "done"
    quit()



