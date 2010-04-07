#!/usr/bin/env python
#coding=utf8

import time
import socket
import xml.sax
import device
import threading
from common import Action, Actionlog, Argument, Assignment, Event

class State:
    """
    Ist eine Informationssammlung, was der Client gerade über sich weiß.
    Wie weit gefahren?
    Wie weit gedreht?
    Ist der Saugkopft unten?
    Was sagen die Sensoren?
    """

    def __init__(self, actionlog, cb_process):
        self.actionlog = actionlog
        self.dict = {}
        self.cb_anyAction = cb_process
        self.devices = \
            { "engine": device.Device('/tmp/dev_engine',
                                      lambda data: self.update("engine", float(data)),
                                      True, True),
              "head":   device.Device('/tmp/dev_head',
                                      lambda data: self.update("head", float(data == "down")),
                                      True, True),
              "left":   device.Device('/tmp/dev_left',
                                      lambda data: self.update("left", float(data)),
                                      True, True),
              "front":  device.Device('/tmp/dev_front',
                                      lambda data: self.update("front", float(data)),
                                      True, True),
              "right":  device.Device('/tmp/dev_right',
                                      lambda data: self.update("right", float(data)),
                                      True, True) }
        self.devices["engine"].write("reset")

        self.update("engine:drive", 0.0)
        self.update("engine:turn", 0.0)
        self.update("head:move", 0.0)
        self.update("front:distance", 1.0)
        self.update("left:distance", 1.0)
        self.update("right:distance", 1.0)

    def __del__(self):
        self.devices["engine"].close()
        self.devices["head"].close()
        self.devices["left"].close()
        self.devices["front"].close()
        self.devices["right"].close()
        self.devices = None

    def getValue(self, key):
        """ Gibt den value zu key """
        value = None
        if self.dict.has_key(key):
            value = self.dict[key]
        return value

    def sendAction(self, key, value):
        action = key.split(":")[0]
        self.actionlog.update(action, value)

    def update(self, key, value, process=True):
        """ Erstellt/Aktualisiert einen Wert """
        self.dict[key] = value
        self.sendAction(key, value)
        if process and self.cb_anyAction:
            self.cb_anyAction()

class Connector(threading.Thread):
    """
    Stellt die Verbindung zum Server her
    """
    def __init__(self):
        threading.Thread.__init__(self)
        self.host = "127.0.0.1"
        self.port = 29875
        self.connected = False
        self.socket = None
        self.data = ''
        self.stop = False
        self.start()

    def connect(self):
        if not self.connected:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.connected = True

    def disconnect(self):
        if self.connected:
            print "disconnecting..."
            self.write("DISCO")
            self.socket.close()
            self.connected = False

    def run(self):
        self.connect()
        self.read()
        self.disconnect()

    def read(self):
        truedata=''
        while not self.stop:
            print "thread reads..."
            data = self.socket.recv(4096)
            if not data:
                self.stop = True
                break
            truedata += data
            if "</what-to-do>" in data:
                self.data=truedata
                truedata=''
            if self.data == "DISCO":
                self.stop = True

    def write(self,data):
        self.socket.send(data)

    def getData(self):
        data = self.data
        self.data = ''
        return data

class XmlHandler(xml.sax.ContentHandler):
    """
    Handles XML.SAX events
    """

    def __init__(self, client):
        self.client = client
        self.openAssignment = None

    def startElement(self,name,attrs):
        print "start", name

        if name == "assignment":
            actionStart = None
            actionEnd = None
            id = 0
            for key,value in attrs.items():
                if key == "start":
                    actionStart = Action(value, "false")
                elif key == "end":
                    actionEnd = Action(value, "false")
                elif key == "id":
                    id = int(value)
            self.openAssignment = Assignment(id, actionStart, actionEnd)
            self.client.assignments.append(self.openAssignment)

        elif name == "event":
            arg1 = None
            arg2 = None
            compare = None
            action = None
            then = None
            final = None

            for key,value in attrs.items():
                if key == "ifarg1":
                    arg1 = Argument(value)

                elif key == "ifarg2":
                    arg2 = Argument(value)

                elif key == "ifcompare":
                    compare = value

                elif key == "then":
                    then = value

                elif key == "final":
                    final = value

            action = Action(then, final)
            self.openAssignment.events.append(Event(arg1, arg2, compare, action))



class Client:
    """
    Die Zusammenfassung aller Instrumente und Main-Klasse.
    """
    transmission_id = None            # Identifikation der letzten Kommunikation
    assignment      = None            # Letztes ausgeführtes Assignment
    assignments     = []
    actionlog       = None
    stateholder     = None
    connection      = None

    def __init__(self):
        self.actionlog = Actionlog()
        self.stateholder = State(self.actionlog, self.process)
        self.connection = Connector()

    def __del__(self):
        if self.connection <> None:
            self.connection.disconnect()

    def getNextAssignments(self):
        """ holt neue Aufgaben vom Server """
        self.assignment    = None
        self.assignments   = []
        data = self.connection.getData()
        if data:
            print data
            xml.sax.parseString(data, XmlHandler(self))

        return 0

    def nextAssignment(self):
        """ aktiviert das nächste Assignment """
        activated = False
        if self.assignment <> None:
            activated = self.assignment.active

        if not activated:
            for a in self.assignments:
                if self.assignment == None or self.assignment.id < a.id:
                    activated = self.startAssignment(a.id)
                    break
        return activated

    def startAssignment(self, id):
        """ Startet ein Assignment und setzt entsprechend lokale Variablen """
        found = False
        a = next((a for a in self.assignments if a.id == id), None)
        if a <> None:
            found = True
            self.assignment = a
            self.assignment.start(self.stateholder)
        return found

    def sendActionlog(self):
        """ unterrichtet den Server """
        return 1

    def run(self):
        """ Main loop """
        active = 0
        while 1:
            time.sleep(1)
            # erstes/nächstes Assignment ausführen
            active = self.nextAssignment()
            # sekündliche Prüfung
            if active:
                self.process()
            # wenn nichts mehr zu tun ist
            # Verbindugn zum Server aufbauen,
            # Bericht an den Server senden und neue Aufgaben holen
            else:
                self.sendActionlog()
                self.getNextAssignments()

        # Serververbindung trennen
        if self.connection <> None:
            self.connection.disconnect()

    def process(self):
        if self.assignment:
            self.stateholder.update("running", time.time() - self.assignment.starttime, process=False)
            self.assignment.process(self.stateholder)

if __name__ == '__main__':
    print "init client"
    client = Client()
    print "run client"
    client.run()
    print "done"



