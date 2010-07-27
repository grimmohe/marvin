#!/usr/bin/env python
#coding=utf8

from common import Connector

class Device:
    """
    Ein Netzwerkdevice, mit dem Daten zwischen Client und Simulator ausgetauscht werden.
    """

    cb_readevent = None

    def __init__(self, devname, cb_event):
        print "new dev: " + devname
        self.con = Connector('127.0.0.1', 29874)
        self.con.setDataIncomingCb(self.read)
        self.name = devname
        self.cb_readevent = cb_event

    def __del__(self):
        self.close()

    def read(self, connection, data):
        if len(data):
            data = data.split("#")
            if data[0] == self.name:
                if len(data) < 2:
                    # here once raised an index error exception and this should show why
                    print "item:", data
                self.cb_readevent(data[1])
        return 1

    def write(self, data):
        self.con.write(self.name + "#" + data)
        return 1

    def close(self):
        if self.con:
            self.con.stop = True
            self.con.disconnect(True)
            self.con = None
