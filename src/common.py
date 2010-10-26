#!/usr/bin/env python
#coding=utf8

import socket
import time
import re
import network
import xml.sax
from copy import copy
import callback as cb

class Actionlog:
    """
    Eine Aufzeichnung der letzten Aktivitäten seit Rückmeldung an den Server.
    """

    """ Aktionsupdates, die für die Log ignoriert werden """
    IGNORE = ("running")

    """ fortlaufendes update """
    SERIAL = ("engine:distance", "engine:turned")

    def __init__(self):
        self.clear()

    def __del__(self):
        self.quit()

    def clear(self):
        self.actions = []

    def getActionValue(self, action):
        for entry in self.actions:
            if entry.action == action:
                return entry.value
        return None

    def quit(self):
        self.actions = None

    def readXml(self, data):
        self.clear()
        xml.sax.parseString(data, ActionlogXmlHandler(self))
        return 1

    def toXml(self):
        cReturn = '<?xml version="1.0" encoding="UTF-8"?><what-have-i-done>'
        # reverse(), damit die Aktionen in der Reihenfolge des Geschehens ausgegeben werden
        self.actions.reverse()
        for action in self.actions:
            cReturn += action.toXml()
        # und wieder zurück verdrehen
        self.actions.reverse()
        cReturn += "</what-have-i-done>"
        return cReturn

    """
    Das Log bekommt hier jede Veränderung mitgeteilt.
    Engine-Events und die Laufzeit verändern sich ständig und sollten nicht jedes mal neu
    eingetragen werden.
    Als Ergebnis wird eine Liste self.actions produziert, die z.B. folgendes aussagt:
    1 Meter gefahren, Sensor vorne auf 0.5, 90° gedreht, 2 Meter gefahren
    """
    def update(self, action, value):
        if not (action in self.IGNORE):
            if len(self.actions) and self.actions[0].action == action:
                self.actions[0].value = value
            else:
                start_value = 0.0
                last_value = self.getActionValue(action)
                if action in self.SERIAL:
                    # Wenn der letzte Wert von engine:distance < dem aktuellen Update, hat die
                    # Engine nicht angehalten. Es kamen nur andere Events dazwischen. Damit die
                    # Distanz ab der Sensoränderung dokumentiert ist, wird der erste Wert als
                    # Startwert übernommen.
                    if last_value and ((last_value > 0 and last_value <= value) or (last_value < 0 and last_value >= value)):
                        start_value = last_value
                elif last_value == value:
                    return 1

                self.actions.insert(0, ActionlogEntry(action, value, start_value))
        return 1


class ActionlogEntry:
    """
    Eintrag im Actionlog beschreibt einen Zustand während eines Vorganges (id)
    """

    def __init__(self, action, value, start_value = 0.0):
        self.action = action
        self.value = value
        self.start_value = start_value

    def toXml(self):
        if type(self.value) in (int, float):
            value = str(self.value - self.start_value)
        else:
            value = str(self.value)
        return "<" + self.action + " value='" + value + "'" + "/>"

class ActionlogXmlHandler(xml.sax.ContentHandler):
    """
    Handles XML.SAX events to create ActionlogEntry
    """
    def __init__(self, actionlog):
        self.actionlog = actionlog

    def startElement(self,name,attrs):
        value = 0.0
        if name <> "what-have-i-done":
            for attr,val in attrs.items():
                if attr == "value":
                    try:
                        value = float(val)
                    except ValueError:
                        value = val
            self.actionlog.actions.append(ActionlogEntry(name, value))
        return 0


class Action:
    """
    Ausführen von/ direkte weitergabe an die devices
    """
    # dev:command=1
    def __init__(self, args, final, assignment):
        self.actions = []
        for arg in args.split(";"):
            a = {"value": None, "device_id": None, "command": None, "next_id": None, "suicide": False}
            if "a#=" in arg:
                a["next_id"] = int(arg.split("=")[1])
            elif "=" in arg and ":" in arg:
                arg = arg.split("=", 2)
                a["value"] = arg[1]
                arg = arg[0].split(":", 2)
                a["device_id"] = arg[0]
                a["command"] = arg[1]
            self.actions.append(a)
        self.final = (final == "true")
        self.assignment = assignment

    def add(self, action_item):
        self.actions.append(action_item)

    def execute(self, states):
        for a in self.actions:
            if states.devices.has_key(a["device_id"]):
                print "Action.execute", a["device_id"], a["command"] + "=" + a["value"]
                states.devices[a["device_id"]].write(a["command"] + "=" + a["value"])
            elif a["next_id"] and self.assignment and self.assignment.parentAssignment:
                if self.final:
                    new_action = copy(a)
                    new_action["suicide"] = True
                    self.assignment.stopAction.add(new_action)
                else:
                    self.assignment.parentAssignment.startSubAssignment(a["next_id"], states)
            if a["suicide"]:
                self.actions.remove(a)
        return not self.final

    def quit(self):
        self.assignment = None

    def toXml(self, value_only=False):
        cReturn = ""
        for a in self.actions:
            if a["next_id"]:
                cReturn += ";a#=" + str(a["next_id"])
            else:
                cReturn += ";" + self.device_id + ":" + self.command + "=" + self.value
        cReturn = cReturn.strip(";")
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
    Ein Assignment kann Sub-Assignemnts haben, die sich untereinander aufrufen, bis ein
    finales Event im Main-Assignment zum Stop führt.
    Abschließend wird, wenn belegt, stop_event verarbeitet.
    """

    def __init__(self, id, startAction, stopAction, parent=None):
        self.id = id
        self.active = False
        self.startAction = startAction
        self.stopAction = stopAction
        self.events = []
        self.subAssignments = []
        self.parentAssignment = parent
        self.lastprocessing = 0
        self.starttime = None

    def countActiveSub(self):
        count = 0
        for sub in self.subAssignments:
            if sub.active:
                count += 1
        return count

    def quit(self):
        for event in self.events:
            event.quit()
        self.events = None
        for sub in self.subAssignments:
            sub.quit()
        if self.startAction:
            self.startAction.quit()
            self.startAction = None
        if self.stopAction:
            self.stopAction.quit()
            self.stopAction = None
        self.parentAssignment = None

    def start(self, states):
        """ aktiviert das Assignment """
        self.active = True
        self.starttime = time.time()
        print "Assignment.start", self.id, "Count Subs:", len(self.subAssignments)
        if self.startAction:
            self.startAction.execute(states)
        if len(self.subAssignments):
            self.subAssignments[0].start(states)

    def startSubAssignment(self, id, states):
        sub = next((sub for sub in self.subAssignments if sub.id == id), None)
        if sub:
            sub.start(states)
        return (sub <> None)

    def toXml(self):
        cReturn = "<assignment id='" + str(self.id) + "'"

        if self.startAction:
            cReturn += " start='" + self.startAction.toXml(value_only=True) + "'"
        if self.stopAction:
            cReturn += " end='" + self.stopAction.toXml(value_only=True) + "'"

        cReturn += ">"

        for event in self.events:
            cReturn += event.toXml()

        for sub in self.subAssignments:
            cReturn += sub.toXml()

        cReturn += "</assignment>"

        return cReturn

    def process(self, states):
        """ verarbeitet neue Events """
        if not self.active:
            return 1

        goon = len(self.events) or self.countActiveSub()

        for event in self.events:
            goon = goon and event.check(states)

        for sub in self.subAssignments:
            goon = goon and sub.process(states)

        if not goon:
            self.stop(states)

        return goon or (self.parentAssignment and self.parentAssignment.countActiveSub())

    def stop(self, states, superior=False):
        """
        Deaktiviert das Assignment und seine Subs. Superior wird hier nur von stop() selbst gesetzt,
        um die stopAction nur auf oberster Ebene auszuführen.
        """
        print "Assignment.stop", self.id
        for sub in self.subAssignments:
            if sub.active:
                sub.stop(states, True)
        if self.stopAction and (not superior):
            self.stopAction.execute(states)
        self.active = False

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
            then = ""
            final = None

            for key,value in attrs.items():
                if key == "ifarg1":
                    arg1 = value

                elif key == "ifarg2":
                    arg2 = value

                elif key == "ifcompare":
                    compare = value

                elif key == "then":
                    then = value

                elif key == "final":
                    final = value

            arg1suffix = arg1.split(":")
            arg1 = arg1suffix[0]
            if len(arg1suffix) > 1: arg1suffix = ":" + arg1suffix[1]
            else: arg1suffix = ""

            arg2suffix = arg2.split(":")
            arg2 = arg2suffix[0]
            if len(arg2suffix) > 1: arg2suffix = ":" + arg2suffix[1]
            else: arg2suffix = ""

            if len(arg1) and len(arg2):
                for rarg1 in arg1.split(","):
                    for rarg2 in arg2.split(","):
                        action = Action(then, final, self.openAssignment)
                        self.openAssignment.events.append(Event(Argument(rarg1 + arg1suffix), Argument(rarg2 + arg2suffix), compare, action))

    def endElement(self, name):
        if name == "assignment" and self.openAssignment:
            self.openAssignment = self.openAssignment.parentAssignment


class Argument:
    """
    Ist ein statischer Wert oder eine Abfrage an State.
    """
    ARG_STATIC = 1
    ARG_STATE = 2

    def __init__(self, arg):
        # nur float (0.0)
        if re.match("^(-?[\d]+\.?[\d]*|-?[\d]*\.?[\d]+)$", arg, 0):
            arg_typ = self.ARG_STATIC
            arg_key = float(arg)
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

    def quit(self):
        pass

    def toXml(self):
        cReturn = ""
        if self.typ == self.ARG_STATIC:
            cReturn = str(self.key)
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

        arg1 = None
        arg2 = None

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

        #print arg1, self.compare, arg2

        if match:
            print "MATCH: ", arg1, self.compare, arg2
            goon = self.action.execute(states)
        return goon

    def quit(self):
        if self.arg1:
            self.arg1.quit()
            self.arg1 = None
        if self.arg2:
            self.arg2.quit()
            self.arg2 = None
        if self.action:
            self.action.quit()
            self.action = None

    def toXml(self):
        cReturn = "<event" \
                + " ifarg1='" + self.arg1.toXml() + "'" \
                + " ifarg2='" + self.arg2.toXml() + "'" \
                + " ifcompare='" + self.compare + "'" \
                + self.action.toXml() \
                + "/>"
        return cReturn


class Connector(network.networkConnection):
    """
    Stellt die Verbindung zum Server her
    """
    def __init__(self, ip, port, autoReconnect=False):
        network.networkConnection.__init__(self)
        self.host = ip
        self.port = port
        self.connected = False
        self.autoReconnect = autoReconnect
        self.deamon = True
        self.start()

    def run(self):
        if self.autoReconnect:
            self.cbl["onExternDisconnection"].add(cb.CallbackCall(self.disconnection))
            if not self.tryConnectEndless():
                return False
        else:
            if not self.connect():
                return False
        network.networkConnection.run(self)
        return True


    def tryConnectEndless(self):
        self.socket = None
        while True:
            print self.name + ": connecting.. " + str(self.host) + ":" + str(self.port)
            if self.connect():
                self.cbDisconnect = self.disconnection
                return True
            time.sleep(5)


    def connect(self):
        sock = None
        if not self.connected:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect((self.host, self.port))
            except Exception, e:
                print e.message
                return False
            print self.name + ": connection established"
            self.socket = sock
            self.connected = True
            return True

    def disconnect(self, withDisco):
        if self.connected:
            print self.name + ": disconnecting (withDisco:"+str(withDisco)+")..."
            network.networkConnection.disconnect(self, withDisco)
            self.connected = False

    def disconnection(self, connection):
        print self.name + ": disconnection..."
        self.connected = False
        self.reader = None
        if self.autoReconnect:
            self.tryConnectEndless()
        self.reader = network.networkConnectionReader(self)



class SortedList(object):

    def __init__(self, key):
        self._key = key
        self._list = []

    def append(self, value):
        index = self.find(value)
        self._list.insert(index, value)
        return value

    def clear(self):
        self._list = []

    def contains(self, value):
        index = self.find(value)
        if index < len(self._list):
            return value == self._list[index]
        return False

    def count(self):
        return len(self._list)

    def copy(self, sl):
        for o in sl._list:
            self.append(o)

    def find(self, value):
        """ returns index of value. if value is not found, index is where it should be inserted """
        lo = 0
        hi = len(self._list)
        while lo < hi:
            mid = (lo+hi)//2
            if self._key(value, self._list[mid]) > 0:
                lo = mid+1
            else:
                hi = mid
        return lo

    def get(self, index):
        return self._list[index]

    def pop(self, index):
        return self._list.pop(index)

    def remove(self, value):
        index = self.find(value)
        if self._list[index] == value:
            self._list.pop(index)
            return True
        return False

