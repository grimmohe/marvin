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

    start_event = None
    stop_event  = None

    def __init__(self):
        pass

    def run(self):
        pass

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
    def __init__(self):
        pass

    def run(self):
        pass

if __name__ == '__main__':
    client = Client()
    client.run()



