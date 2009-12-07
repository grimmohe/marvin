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

    filename = None
    cb_readevent = None
    wm = None
    wdd = None
    file = None
    watchmask = pyinotify.EventsCodes.FLAG_COLLECTIONS["OP_FLAGS"]["IN_MODIFY"]

    def __init__(self, filename, cb_event):
        self.filename = filename
        self.file = os.open(self.filename, os.O_RDWR | os.O_CREAT)
        os.lseek(self.file, 0, os.SEEK_END)
        self.cb_readevent = cb_event

        # Neuen Inotifier erzeugen
        self.wm = pyinotify.WatchManager()
        self.fileevent = FileEvent()
        self.fileevent.cb_modify = self.read
        self.notifier = pyinotify.ThreadedNotifier(self.wm, self.fileevent)
        self.notifier.start()
        self.wdd = self.wm.add_watch(self.filename, self.watchmask, rec=True)

    def __del__(self):
        self.wm.rm_watch(self.wdd.values())
        self.notifier.stop()
        print "device stop"

    def read(self):
        stream = os.read(self.file, 2048)
        for data in string.split(stream, "\n"):
            if len(data) > 0:
                self.cb_readevent(data)
        return 1

    def write(self, data):
        os.write(self.file, data + "\n")
        print "device", self.filename, "write:", data
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


