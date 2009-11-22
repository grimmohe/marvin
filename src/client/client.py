#!/usr/bin/env python
#coding=utf8

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

    def __init__(self):
        pass

    def start(self):
        """ aktiviert das Assignment """
        self.active = True
        if self.start_event <> None:
            self.start_event()
        #TODO: keep everyone waiting

    def process(self):
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
    def __init__(self):
        pass

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
    assignment_id   = None            # Letztes ausgeführtes Assignment
    assignments     = []
    actionlog       = None

    def __init__(self):
        self.actionlog = Actionlog()

    def getNextAssignments(self):
        """ holt neue Aufgabn vom Server """
        self.assignment_id = None
        self.assignments   = []
        return 1

    def nextAssignment(self):
        """ aktiviert das nächste Assignment """
        activated = False
        for a in self.assignments:
            if self.assignment_id == None | self.assignment_id < a.id:
                activated = self.startAssignment(a.id)
                break
        return activated

    def startAssignment(self, id):
        """ Startet ein Assignment und setzt entsprechend lokale Variablen """
        found = False
        a = next((a for a in self.assignments if a.id == id), None)
        if a <> None:
            found = True
            self.assignment_id = a.id
            a.start()
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



