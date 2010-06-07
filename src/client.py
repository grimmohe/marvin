#!/usr/bin/env python
#coding=utf8

import time
import xml.sax
import device
from common import Actionlog, AssignmentXmlHandler, Connector

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
        self.devices = \
            { "engine": device.Device('engine',
                                      lambda data: self.debugstep("engine:"+data.split("=")[0], data)),
              "head":   device.Device('head',
                                      lambda data: self.debugstep("head:move", data)),
              "left":   device.Device('left',
                                      lambda data: self.debugstep("left:distance", data)),
              "front":  device.Device('front',
                                      lambda data: self.debugstep("front:distance", data)),
              "right":  device.Device('right',
                                      lambda data: self.debugstep("right:distance", data)) }
        self.devices["engine"].write("reset=1")

        self.update("engine:drive", 0.0)
        self.update("engine:turned", 0.0)
        self.update("head:move", 0.0)
        self.update("front:distance", 1.0)
        self.update("left:distance", 1.0)
        self.update("right:distance", 1.0)

    def clearActionlog(self):
        self.actionlog.clear()

    #TODO: do it right
    def debugstep(self, key, value):
        value = value.split("=")[1]

        if key == "head:move":
            self.update(key, float(value == "down"))
        elif key == "engine:turn":
            if value == "left":
                self.update(key, -1.0)
            else:
                self.update(key, float(value == "right"))
        else:
            self.update(key, float(value))

    def __del__(self):
        self.quit()

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
        self.assignment      = None            # Letztes ausgeführtes Assignment
        self.assignments     = []
        self.stateholder = State(self.process)
        self.connection = Connector('127.0.0.1',29875)

    def __del__(self):
        if self.connection:
            self.connection.disconnect()

    def getNextAssignments(self):
        """ holt neue Aufgaben vom Server """
        self.assignment    = None
        self.assignments   = []
        data = self.connection.getData()
        if data:
            xml.sax.parseString(data, AssignmentXmlHandler(self))

        return 0

    def runNextAssignment(self):
        """ aktiviert das nächste Assignment """
        activated = False

        if self.assignment:
            activated = self.assignment.active

        if not activated:
            for a in self.assignments:
                if self.assignment == None or a.id > self.assignment.id:
                    self.assignment = a
                    self.assignment.start(self.stateholder)
                    activated = True
                    break
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
            self.connection.disconnect()

    def process(self):
        if (not self.process_active) and self.assignment:
            self.process_active = True
            try:
                self.stateholder.update("running", time.time() - self.assignment.starttime, process=False)
                self.assignment.process(self.stateholder)
            except:
                pass # this happens only while debugging
            self.process_active = False

    def quit(self):
        self.assignment = None
        for a in self.assignments:
            a.quit()
        self.assignments = None

        self.connection.quit()
        self.connection = None

        self.stateholder.quit()
        self.stateholder = None


if __name__ == '__main__':
    print "init client"
    client = Client()
    print "run client"
    client.run()
    client.quit()
    print "done"
    quit()



