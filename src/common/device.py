#!/usr/bin/env python
#coding=utf8

import os
import pyinotify

class Device:
    """
    Beobachtet eine Datei, indem regelmäßig read() aufgerufen wird.
    Schreibt in selbige Datei mit write(data).
    Sollten mit read() neue Informationen gelesen werden, wird
    cb_readevent ausgelöst.
    """

    filename = None
    cb_readevent = None
    last_write = None
    last_read = None
    wm = None
    wdd = None
    file = None
    watchmask = pyinotify.EventsCodes.FLAG_COLLECTIONS["OP_FLAGS"]["IN_MODIFY"]

    def __init__(self, filename, cb_event):
        self.filename = filename

        # Neuen Inotifier erzeugen
        self.wm = WatchManager()
        self.fileevent = FileEvent()
        fileevent.cb_modify = self.read
        self.notifier = ThreadedNotifier(wm, fileevent)
        self.notifier.start()
        self.wdd = self.wm.add_watch(self.file, watchmask, rec=True)
        self.file = os.open(filename, os.O_CREAT | os.O_RDWR | os.O_SYNC)

    def __del__(self):
        self.rm_watch(self.wdd.values())
        self.notifier.stop()

    def read(self):
        data = os.read(self.file, 80)
        if len(data) > 0:
            self.cb_readevent(data)
            self.last_read = data
        return 1

    def write(self, data):
        if data <> self.last_write:
            os.write(self.file, data)
            os.lseek(self.file, 0, os.SEEK_END)
            self.last_write = data
        return 1

class FileEvent(pyinotify.ProcessEvent):

    cb_modify = None

    def process_IN_MODIFY(self, event):
        self.cb_modify()

