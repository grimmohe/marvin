#!/usr/bin/env python
#coding=utf8

import time
import re
import xml.sax

class Actionlog:
    """
    Eine Aufzeichnung der letzten Aktivitäten seit Rückmeldung an den Server.
    """
    def __init__(self):
        self.clear()
        
    def __del__(self):
        self.actions = None
        
    def clear(self):
        self.actions = []

    def readXml(self, xml):
        xml.sax.parseString(xml, ActionlogXmlHandler(self))
        return 1

    def toXml(self):
        cReturn = '<?xml version="1.0" encoding="UTF-8"?><what-have-i-done>'
        for action in self.actions:
            cReturn += action.toXml()
        cReturn += "</what-have-i-done>"
        return cReturn

    def update(self, action, value):
        print "action", action, value
        if ( len(self.actions) == 0
             or not self.actions[len(self.actions)-1].update(action, value) ) :
            self.actions.append(ActionlogEntry(action, value))
        return 1


class ActionlogEntry:
    """
    Eintrag im Actionlog beschreibt eine Aktion mit andauernen Zuständen
    """
    def __init__(self, action, value, start=None):
        self.action = action
        self.value = value
        if start <> None:
            self.start_value = start
        else:
            self.start_value = value

    def toXml(self):
        return "<" + self.action  \
               + " value='" + str(int((self.value - self.start_value) * 100)) + "'/>"

    def update(self, action, value):
        iReturn = 0
        if self.action == action:
            iReturn = 1
            self.value = value
        return iReturn

class ActionlogXmlHandler(xml.sax.ContentHandler):
    """
    Handles XML.SAX events to create ActionlogEntry
    """
    def __init__(self, actionlog):
        self.actionlog = actionlog

    def startElement(self,name,attrs):
        val = 0.0
        for attr,val in attrs:
            if attr == "value":
                value = float(val) / 100
        if name <> "what-have-i-done":
            self.actionlog.actions.append(ActionlogEntry(name, value, 0.0))
        return 0


class Action:
    """
    Ausführen von/ direkte weitergabe an die devices
    """
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

    def toXml(self, value_only=False):
        cReturn = self.device_id + ":" + self.command + "=" + self.value
        if not value_only:
            cReturn = "then='" + cReturn + "' final='" + ["false", "true"][self.final] + "'"
        return cReturn

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

    def toXml(self):
        cReturn = "<assignment id='" + str(self.id) + "'"

        if self.startAction:
            cReturn += " start='" + self.startAction.toXml(value_only=True) + "'"
        if self.stopAction:
            cReturn += " end='" + self.stopAction.toXml(value_only=True) + "'"

        cReturn += ">"
        for event in self.events:
            cReturn += event.toXml()
        cReturn += "</assignment>"

        return cReturn

    def process(self, states):
        """ verarbeitet neue Events """
        if not self.active:
            return 0

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

    def toXml(self):
        cReturn = ""
        if self.typ == self.ARG_STATIC:
            cReturn = str(int(self.key * 100))
        elif self.typ == self.ARG_STATE:
            cReturn = self.key
        return cReturn


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

    def toXml(self):
        cReturn = "<event" \
                + " ifarg1='" + self.arg1.toXml() + "'" \
                + " ifarg2='" + self.arg2.toXml() + "'" \
                + " ifcompare='" + self.compare + "'" \
                + self.action.toXml() \
                + "/>"
        return cReturn
