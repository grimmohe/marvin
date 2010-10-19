#!/usr/bin/env python
#coding=utf8

from common import Connector
import callback as cb

class Device:
    """
    Ein Netzwerkdevice, mit dem Daten zwischen Client und Simulator ausgetauscht werden.
    """

    cb_readevent = None

    def __init__(self, devname, cb_event):
        print "new dev: " + devname
        self.con = Connector('127.0.0.1', 29874, autoReconnect=True)
        self.con.cbl["onDataIncoming"].add(cb.CallbackCall(self.read))
        self.name = devname
        self.cb_readevent = cb_event

    def __del__(self):
        self.close()

    def read(self, attributes):
        connection = attributes["networkConnection"]
        data= attributes["data"]
        if len(data):
            lines= data.split('\n')
            for line in lines:
                if len(line):
                    items = line.split("#")
                    if items[0] == self.name:
                        if len(items) < 2:
                            # here once raised an index error exception and this should show why
                            print "item:", line
                        self.cb_readevent(items[1])
            return True
        return False

    def write(self, data):
        self.con.write(self.name + "#" + data)
        return 1

    def close(self):
        if self.con:
            self.con.stop = True
            self.con.disconnect(True)
            self.con = None
