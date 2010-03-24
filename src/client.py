#!/usr/bin/env python
#coding=utf8

import time
import socket
import xml.sax
import device

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
    id     = None
    active = False
    events = []
    lastprocessing = 0
    starttime = None

    startAction = None
    stopAction = None

    def __init__(self, startAction, stopAction):
        self.startAction = startAction
        self.stopAction = stopAction

    def start(self, states):
        """ aktiviert das Assignment """
        self.active = True
        self.starttime = time.time()
        if self.startAction <> None:
            self.startAction.execute()

    def process(self, states):
        """ verarbeitet neue Events """
        if not self.active:
            return 0

        states.update("running", time.time( - self.starttime))
        goon = 1

        for event in self.events:
            goon = goon and event.check(states)

        self.active = goon
        return goon

    def stop(self, states):
        """ deaktiviert das Assignment """
        if self.stopAction <> None:
            self.stopAction.execute()
        self.active = False

class Argument:
    """
    Ist ein statischer Wert oder eine Abfrage an State.
    """
    ARG_STATIC = 1
    ARG_STATE = 2

    def __init__(self, arg_key, arg_typ):
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

        if ">" in self.compare:
            match = match or self.arg1.get(states) > self.arg2.get(states)
        if "<" in self.compare:
            match = match or self.arg1.get(states) < self.arg2.get(states)
        if "=" in self.compare:
            match = match or self.arg1.get(states) == self.arg2.get(states)

        if match:
            goon = self.action.execute()
        return goon

class State:
    """
    Ist eine Informationssammlung, was der Client gerade über sich weiß.
    Wie weit gefahren?
    Wie weit gedreht?
    Ist der Saugkopft unten?
    Was sagen die Sensoren?
    """
    dict = {}
    devices = {}
    cb_anyAction = None

    def __init__(self):
        self.dict = {}
        self.devices = \
            { "engine": device.Device('/tmp/dev_engine',
                                      lambda data: self.update("engine", data),
                                      True, True),
              "head":   device.Device('/tmp/dev_head',
                                      lambda data: self.update("head", data),
                                      True, True),
              "left":   device.Device('/tmp/dev_left',
                                      lambda data: self.update("left", data),
                                      True, True),
              "front":  device.Device('/tmp/dev_front',
                                      lambda data: self.update("front", data),
                                      True, True),
              "right":  device.Device('/tmp/dev_right',
                                      lambda data: self.update("right", data),
                                      True, True) }

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

class Connector:
    """
    Stellt die Verbindung zum Server her
    """
    def __init__(self):
        self.host = "127.0.0.1"
        self.port = "29876"
        self.connected = False
        self.socket = None

    def connect(self):
        if not self.connected:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.connected = True

    def disconnect(self):
        if self.connected:
            self.socket.close()
            self.connected = False

class XmlHandler(xml.sax.ContentHandler):
    """
    Handles XML.SAX events
    """

    def __init__(self):
        pass

    def startDocument(self):
        pass

    def endDocument(self):
        pass

    def startElement(self,name,attrs):
        print "start", name
        for key,value in attrs.items():
            print key,value

    def endElement(self,name):
        print "end", name

    def startElementNS(self,name,qname,attrs):
        print "start ns", name, qname
        for key,value in attrs.items():
            print key,value

    def endElementNS(self,name,qname):
        print "end", name, qname

    def characters(self,data):
        print "characters", data

    def ignorableWhitespace(self):
        print "ignorableWhitespace"

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
        self.connection.socket.send("Gimme")
        data = self.connection.socket.resv(4096)
        self.connection.socket.send("KILL")
        # TODO: parse data
        print data
        return 0

    def nextAssignment(self):
        """ aktiviert das nächste Assignment """
        activated = False
        if self.assignment <> None:
            activated = self.assignment.activ

        if not activated:
            for a in self.assignments:
                if self.assignment == None | self.assignment.id < a.id:
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
                self.connection.connect()
                self.sendActionlog()
                if not self.getNextAssignments():
                    return 0

        # Serververbindung trennen
        if self.connection <> None:
            self.connection.disconnect()

if __name__ == '__main__':
    print "init client"
    client = Client()
    print "run client"
    client.run()
    print "done"



