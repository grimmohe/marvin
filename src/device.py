#!/usr/bin/env python
#coding=utf8

import os
import pyinotify
import string
from client import Connector

class Device:
    """
    Beobachtet eine Datei, indem regelmäßig read() aufgerufen wird.
    Schreibt in selbige Datei mit write(data).
    Sollten mit read() neue Informationen gelesen werden, wird
    cb_readevent ausgelöst.
    """

    cb_readevent = None

    def __init__(self, devname, cb_event):
        self.con = Connection('127.0.0.1', 29874)
        self.con.setDataIncomingCb(self.read())
        self.name = devname
        
    def __del__(self):
        self.close()
        
    def read(self,src):
        data = src.getData()
        if data.split("#")[0] == self.name:
            self.cb_readevent(data)
        return 1

    def write(self, data):
        self.con.write(self.name + "#" + data)
        return 1

    def close(self):
        if self.con:
            self.con.disconnect()

class FileEvent(pyinotify.ProcessEvent):

    cb_modify = None
    lastevent = None

    def process_IN_MODIFY(self, event):
        if self.lastevent <> event:
            self.lastevent = event
            self.cb_modify()


