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
        self.update("engine:turn", 0.0)
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
        self.devices["engine"].close()
        self.devices["head"].close()
        self.devices["left"].close()
        self.devices["front"].close()
        self.devices["right"].close()
        self.devices = None
        self.actionlog = None

    def getValue(self, key):
        """ Gibt den value zu key """
        value = None
        if self.dict.has_key(key):
            value = self.dict[key]
        return value

    def getActionlogXml(self):
        return self.actionlog.toXml()

    def update(self, key, value, process=True):
        """ Erstellt/Aktualisiert einen Wert """
        self.dict[key] = value
        self.actionlog.update(key, value)
        if process and self.cb_anyAction:
            self.cb_anyAction()

class Connector(threading.Thread):
    """
    Stellt die Verbindung zum Server her
    """
    def __init__(self, ip, port):
        threading.Thread.__init__(self)
        self.host = ip
        self.port = port
        self.connected = False
        self.socket = None
        self.data = ''
        self.stop = False
        self.cb_incoming = None
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
        while not self.stop and self.connected:
            data = self.socket.recv(4096)
            if not data:
                self.stop = True
                break
            truedata += data
            if "\n\n" == truedata[-2:]:
                self.data=truedata.strip("\n")
                if self.cb_incoming:
                    self.cb_incoming(self)
                truedata=''

            if self.data == "DISCO":
                self.stop = True

    def write(self,data):
        self.socket.send(data)

    def getData(self):
        data = self.data
        self.data = ''
        return data

    def setDataIncomingCb(self,cb):
        self.cb_incoming = cb

class AssignmentXmlHandler(xml.sax.ContentHandler):
    """
    Handles XML.SAX events
    """
    def __init__(self, client):
        self.client = client
        self.openAssignment = None

    def startElement(self,name,attrs):

        if name == "assignment":
            actionStart = None
            actionEnd = None
            id = 0
            for key,value in attrs.items():
                if key == "start":
                    actionStart = Action(value, "false", None)
                elif key == "end":
                    actionEnd = Action(value, "false", None)
                elif key == "id":
                    id = int(value)
            if self.openAssignment:
                parent = self.openAssignment
            else:
                parent = None

            self.openAssignment = Assignment(id, actionStart, actionEnd, parent=parent)
            if actionStart:
                actionStart.assignment = self.openAssignment
            if actionEnd:
                actionEnd.assignment = self.openAssignment

            if parent:
                parent.subAssignments.append(self.openAssignment)
            else:
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

            action = Action(then, final, self.openAssignment)
            self.openAssignment.events.append(Event(arg1, arg2, compare, action))

    def endElement(self, name):
        if name == "assignment" and self.openAssignment:
            self.openAssignment = self.openAssignment.parentAssignment

class Client:
    """
    Die Zusammenfassung aller Instrumente und Main-Klasse.
    """
    transmission_id = None            # Identifikation der letzten Kommunikation
    assignment      = None            # Letztes ausgeführtes Assignment
    assignments     = []
    stateholder     = None
    connection      = None

    def __init__(self):
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
                if self.assignment == None or self.assignment.id < a.id:
                    self.assignment = a
                    self.assignment.start(self.stateholder)
                    activated = True
                    break
        return activated

    def sendActionlog(self):
        """ unterrichtet den Server """
        xml = self.stateholder.getActionlogXml()
        if xml <> '<?xml version="1.0" encoding="UTF-8"?><what-have-i-done></what-have-i-done>':
            print xml
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
        if self.assignment:
            try:
                self.stateholder.update("running", time.time() - self.assignment.starttime, process=False)
                self.assignment.process(self.stateholder)
            except:
                pass # this happens only while debugging

if __name__ == '__main__':
    print "init client"
    client = Client()
    print "run client"
    client.run()
    print "done"
    quit()



