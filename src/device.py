#!/usr/bin/env python
#coding=utf8

import os
import pyinotify
import string

class Device:
    """
    Beobachtet eine Datei, indem regelmäßig read() aufgerufen wird.
    Schreibt in selbige Datei mit write(data).
    Sollten mit read() neue Informationen gelesen werden, wird
    cb_readevent ausgelöst.
    """

    filename_in = None
    filename_out = None
    cb_readevent = None
    wm = None
    wdd = None
    file_in = None
    file_out = None
    watchmask = pyinotify.EventsCodes.FLAG_COLLECTIONS["OP_FLAGS"]["IN_MODIFY"]

    def __init__(self, filebasename, cb_event, truncate=False):
        
        """ initialize file descriptors """
        self.filename_in = filebasename + "_in"
        self.filename_out = filebasename + "_out"
        
        self.file_in = os.open(self.filename_in, os.O_RDONLY | os.O_CREAT)
        self.file_out = os.open(self.filename_out, os.O_WRONLY | os.O_CREAT)
        
        if truncate:
            os.ftruncate(self.file_out, 0)
            
        os.lseek(self.file_in, 0, os.SEEK_END)
        os.lseek(self.file_out, 0, os.SEEK_END)
        
        """ what function to call on read event """
        self.cb_readevent = cb_event

        # Neuen Inotifier erzeugen
        self.wm = pyinotify.WatchManager()
        self.fileevent = FileEvent()
        self.fileevent.cb_modify = self.read
        self.notifier = pyinotify.ThreadedNotifier(self.wm, self.fileevent)
        self.notifier.start()
        self.wdd = self.wm.add_watch(self.filename_in, self.watchmask, rec=True)

    def __del__(self):
        self.wm.rm_watch(self.wdd.values())
        self.notifier.stop()
        print "device", self.filename_in, "stop"

    def read(self):
        stream = os.read(self.file_in, 2048)
        """print self.filename, "readed", stream"""
        
        for data in string.split(stream, "\n"):
            if len(data) > 0:
                """print "device:", self.filename, "readed:", data"""
                self.cb_readevent(data)
        return 1

    def write(self, data):
        os.write(self.file_out, data + "\n")
        """print "device", self.filename, "write:", data"""
        return 1

    def close(self):
        self.fileevent.cb_modify = None
        self.cb_readevent = None
        os.close(self.file)

class FileEvent(pyinotify.ProcessEvent):

    cb_modify = None
    lastevent = None

    def process_IN_MODIFY(self, event):
        if self.lastevent <> event:
            self.lastevent = event
            self.cb_modify()


