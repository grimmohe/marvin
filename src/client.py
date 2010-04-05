#!/usr/bin/env python
#coding=utf8

import time
import socket
import xml.sax
import device
import threading
import re

class Action:
    """ Ausführen von/ direkte weitergabe an die devices """
    # dev:command=1
    def __init__(self, args, final):
        args = args.split("=", 2)
        self.value = args[1]
        args = args[0].split(":", 2)
        self.device_id = args[0]
        self.command = args[1]
        self.final = (final == "true")

    def execute(self, states):
        if states.devices.has_key(self.device_id):
            states.devices[self.device_id].write(self.command + "=" + self.value)
        return not self.final

class Assignment:
    """
    Representiert die aktuelle Aufgabe.
    Jede Aufgabe hat Ihre eigenen Events. die in der Hauptschleife Client.run()
    verarbeitet werden.
    Ein Assignment beginnt in der Regel mit einem Event (start_event) ohne
    Bedingung und löst durch z.B. Bewegung weitere Events aus.
    Das Assignment wird durch ein Event beendet.
    Abschließend wird, wenn belegt, stop_event verarbeitet.
    """

    def __init__(self, id, startAction, stopAction):
        self.id = id
        self.active = False
        self.startAction = startAction
        self.stopAction = stopAction
        self.events = []
        self.lastprocessing = 0
        self.starttime = None

    def start(self, states):
        """ aktiviert das Assignment """
        self.active = True
        self.starttime = time.time()
        if self.startAction <> None:
            self.startAction.execute(states)

    def process(self, states):
        """ verarbeitet neue Events """
        if not self.active:
            return 0

        states.update("running", time.time() - self.starttime)
        goon = (len(self.events) > 0)

        for event in self.events:
            goon = goon and event.check(states)

        self.active = goon
        return goon

    def stop(self, states):
        """ deaktiviert das Assignment """
        if self.stopAction <> None:
            self.stopAction.execute(states)
        self.active = False

class Argument:
    """
    Ist ein statischer Wert oder eine Abfrage an State.
    """
    ARG_STATIC = 1
    ARG_STATE = 2

    def __init__(self, arg):
        # nur float (0.0)
        if re.match("^([\d]+\.?[\d]*|[\d]*\.?[\d]+)$", arg, 0):
            arg_typ = self.ARG_STATIC
            arg_key = float(arg) / 100
        else:
            arg_typ = self.ARG_STATE
            arg_key = arg
        self.key = arg_key
        self.typ = arg_typ

    def get(self, states):
        ret_val = None
        if self.typ == self.ARG_STATIC:
            ret_val = self.key
        elif self.typ == self.ARG_STATE:
            ret_val = states.getValue(self.key)
        return ret_val

class Event:
    """
    Events stellen Bedingungen und können den Client zu Bewegungen veranlassen.
    """
    def __init__(self, arg1, arg2, compare, action):
        self.arg1 = arg1
        self.arg2 = arg2
        self.compare = compare
        self.action = action

    def check(self, states):
        match = 0
        goon = 1

        if "g" in self.compare:
            arg1 = self.arg1.get(states)
            arg2 = self.arg2.get(states)
            match = match or arg1 > arg2
        if "l" in self.compare:
            arg1 = self.arg1.get(states)
            arg2 = self.arg2.get(states)
            match = match or arg1 < arg2
        if "e" in self.compare:
            arg1 = self.arg1.get(states)
            arg2 = self.arg2.get(states)
            match = match or arg1 == arg2

        if match:
            goon = self.action.execute(states)
        return goon

class State:
    """
    Ist eine Informationssammlung, was der Client gerade über sich weiß.
    Wie weit gefahren?
    Wie weit gedreht?
    Ist der Saugkopft unten?
    Was sagen die Sensoren?
    """

    def __init__(self):
        self.dict = {}
        self.cb_anyAction = None
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

    def update(self, key, value):
        """ Erstellt/Aktualisiert einen Wert """
        self.dict[key] = value
        if self.cb_anyAction:
            self.cb_anyAction(self)

    def getValue(self, key):
        """ Gibt den value zu key """
        value = None
        if self.dict.has_key(key):
            value = self.dict[key]
        return value

class Actionlog:
    """
    Eine Aufzeichnung der letzten Aktivitäten seit Rückmeldung an den Server.
    """
    def __init__(self):
        pass

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

    def read(self):
        truedata=''
        while not self.stop:
            print "thread reads..."
            data = self.socket.recv(4096)
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
        self.stateholder = State()
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
                self.assignment.process(self.stateholder)
            # wenn nichts mehr zu tun ist
            # Verbindugn zum Server aufbauen,
            # Bericht an den Server senden und neue Aufgaben holen
            else:
                self.sendActionlog()
                self.getNextAssignments()

        # Serververbindung trennen
        if self.connection <> None:
            self.connection.disconnect()

if __name__ == '__main__':
    print "init client"
    client = Client()
    print "run client"
    client.run()
    print "done"



