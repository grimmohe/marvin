#!/usr/bin/env python
#coding=utf8

import time
import socket
import xml.sax

class Assignment:
    """
    Representiert die aktuelle Aufgabe.
    Jede Aufgabe hat Ihre eigenen Events. die in der Hauptschleife run()
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

    start_event = None
    stop_event  = None

    startAssignment = None

    def __init__(self, startAssignment):
        self.startAssignment = startAssignment

    def start(self):
        """ aktiviert das Assignment """
        self.active = True
        if self.start_event <> None:
            self.start_event()

    def process(self, states):
        """ verarbeitet neue Events """
        if not self.active:
            return 0
        return 1

    def stop(self):
        """ deaktiviert das Assignment """
        if self.stop_event <> None:
            self.stop_event()
        self.active = False

class Event:
    """
    Events stellen Bedingungen und können den Client zu Bewegungen veranlassen.
    """
    def __init__(self):
        pass

    def check(self):
        pass

class State:
    """
    Ist eine Informationssammlung, was der Client gerade über sich weiß.
    Wie weit gefahren?
    Wie weit gedreht?
    Ist der Saugkopft unten?
    Was sagen die Sensoren?
    """
    dict = {}

    def __init__(self):
        self.dict = {}

    def update(self, key, value):
        """ Erstellt/Aktualisiert einen Wert """
        self.dict[key] = value

    def getValue(self, key):
        """ Gibt den value zu key """
        value = None
        if self.dict.has_key(key):
            value = self.dict[key]
        return value

class Actionlog:
    """
    Eine Aufzeichnungen der letzten Aktivitäten seit Rückmeldung an den Server.
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
    states          = None
    connection      = None

    def __init__(self):
        self.actionlog = Actionlog()
        self.states    = State()
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
            self.assignment.start()
        return found

    def sendActionlog(self):
        """ unterrichtet den Server """
        return 1

    def run(self):
        """ Main loop """
        active = 0
        while 1:
            time.sleep(1)
            #TODO: Heartbeat senden
            # erstes/nächstes Assignment ausführen
            active = self.nextAssignment()
            # wenn nichts mehr zu tun ist
            # Verbindugn zum Server aufbauen,
            # Bericht an den Server senden und neue Aufgaben holen
            if not active:
                self.connection.connect()
                self.sendActionlog()
                if not self.getNextAssignments():
                    return 0

        # Serververbindung trennen

if __name__ == '__main__':
    print "init client"
    client = Client()
    print "run client"
    client.run()
    print "done"



