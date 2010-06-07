#!/usr/bin/env python
#coding=utf8

import socket
import threading
import time
import re
import xml.sax

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
        return "<" + self.action \
            + " value='" + str(int((self.value - self.start_value) * 100)) + "'" \
            + "/>"

class ActionlogXmlHandler(xml.sax.ContentHandler):
    """
    Handles XML.SAX events to create ActionlogEntry
    """
    def __init__(self, actionlog):
        self.actionlog = actionlog

    def startElement(self,name,attrs):
        value = 0.0
        for attr,val in attrs:
            if attr == "value":
                value = float(val) / 100
        if name <> "what-have-i-done":
            self.actionlog.actions.append(ActionlogEntry(name, value))
        return 0


class Action:
    """
    Ausführen von/ direkte weitergabe an die devices
    """
    # dev:command=1
    def __init__(self, args, final, assignment):
        self.value = None
        self.device_id = None
        self.command = None
        self.next_id = None

        if "a#=" in args:
            self.next_id = int(args.split("=")[1])
        elif "=" in args and ":" in args:
            args = args.split("=", 2)
            self.value = args[1]
            args = args[0].split(":", 2)
            self.device_id = args[0]
            self.command = args[1]

        self.final = (final == "true")
        self.assignment = assignment

    def execute(self, states):
        if states.devices.has_key(self.device_id):
            states.devices[self.device_id].write(self.command + "=" + self.value)
        elif self.next_id and self.assignment and self.assignment.parentAssignment:
            self.assignment.parentAssignment.startSubAssignment(self.next_id, states)
        return not self.final

    def quit(self):
        self.assignment = None

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

    def quit(self):
        pass

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

    def quit(self):
        self.cb_incoming = None
        self.socket = None

    def run(self):
        self.connect()
        self.read()
        self.disconnect()

    def read(self):
        truedata=''
        while (not self.stop) and self.connected:
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
