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
        print "device is reading"
        self.file = os.open(self.filename, os.O_CREAT | os.O_RDONLY | os.O_SYNC)
        data = os.read(self.file, 80)
        if len(data) > 0: 
            if self.cb_readevent == None:
                print "device: cb_readevent is None"
            else:
                self.cb_readevent(data)
                self.last_read = data
        else:
            print "device: readed message has 0 length"
            
        self.file = None

        return 1

    def write(self, data):
        if data <> self.last_write:
            self.file = os.open(self.filename, os.O_CREAT | os.O_WRONLY | os.O_SYNC)
            os.write(self.file, data)
            os.lseek(self.file, 0, os.SEEK_END)
            self.last_write = data
            self.file = None
        return 1
    
    def close(self):
        self.fileevent.cb_modify = None
        self.cb_readevent = None
        self.file = None

class FileEvent(pyinotify.ProcessEvent):

    cb_modify = None
    lastevent = None

    def process_IN_MODIFY(self, event):
        if self.lastevent <> event: 
            self.lastevent = event
            self.cb_modify()
        

