#!/usr/bin/env python
#coding=utf8

import time

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

class Client:
    """
    Die Zusammenfassung alle Instrumente und Main-Klasse.
    """
    transmission_id = None            # Identifikation der letzten Kommunikation
    assignment      = None            # Letztes ausgeführtes Assignment
    assignments     = []
    actionlog       = None
    states          = None

    def __init__(self):
        self.actionlog = Actionlog()
        self.states    = State()

    def getNextAssignments(self):
        """ holt neue Aufgaben vom Server """
        self.assignment    = None
        self.assignments   = []
        return 1

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

    def connect(self):
        """ Verbindung zum Server aufbauen """
        return 1

    def disconnect(self):
        """ Verbindung zum Server trennen """
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
                self.conntect()
                self.sendActionlog()
                self.getNextAssignments()

        # Serververbindung trennen
        self.disconnect()

if __name__ == '__main__':
    client = Client()
    client.run()



