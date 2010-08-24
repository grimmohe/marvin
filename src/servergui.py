#!/usr/bin/env python
#coding=utf8


import pygtk
pygtk.require('2.0')
import gtk
import pango
import threading
import server
import logger
import time

class ServerTab:

    def __init__(self, name):

        # main table
        self.mainWidget = gtk.Table(1,1,False)

        # scollablewindow around text edit
        self.scrollableWindow = gtk.ScrolledWindow()
        self.scrollableWindow.set_policy(gtk.POLICY_AUTOMATIC,gtk.POLICY_AUTOMATIC)

        # text input
        self.textView = gtk.TextView()
        self.textBuffer = self.textView.get_buffer()

        # join text and scrollable window
        self.textView.set_wrap_mode(gtk.WRAP_WORD)
        self.scrollableWindow.add(self.textView)

        # start stop buttons
        self.btnstop = gtk.Button("Stop")
        self.btnstop.connect("clicked", lambda w: self.ServerStop())
        self.btnstart = gtk.Button("Start")
        self.btnstart.connect("clicked", lambda w: self.ServerStart())

        self.tooldiv = gtk.HBox(False, 0)
        self.tooldiv.pack_start(self.btnstart, False, 0)
        self.tooldiv.pack_end(self.btnstop, False, 0)

        self.mainWidget.attach(self.scrollableWindow, 0,1,0,1)
        self.mainWidget.attach(self.tooldiv, 0,1,1,2,0,0,0,0)

        self.mainWidget.show_all()
        self.logger = logger.loggerTextBuffer(self.textBuffer)
        self.server = None
        self.name = name

    def ServerStop(self):
        self.logger.log("stop server")
        self.server.srvlis.shutdown()
        self.server=None

    def ServerStart(self):
        self.logger.log("start server")
        if not self.server:
            if self.name == "MarvinServer":
                self.server = server.MarvinServer()
            if self.name == "DeviceServer":
                self.server = server.DeviceServer()
            self.server.srvlis.setLogger(self.logger)
            self.ServerRun(50)
            self.logger.log("done")

    def ServerRun(self, maxTries):
        curTry = 0
        self.server.srvlis.setLogger(self.logger)
        while curTry <= maxTries:
            self.logger.log( "try to run " + self.server.name + " (" + str(curTry) + "/" + str(maxTries) + ")")
            if self.server.run():
                return True
            curTry += 1
            time.sleep(5.0)
        return False


    def getDiv(self):
        return self.mainWidget

class TabBox:

    def __init__(self):
        self.tabs = []
        self.div = gtk.HBox()
        self.lshow = False

    def add(self, name, evnt):
        btn = gtk.Button(name)
        self.tabs.append(btn)
        self.div.pack_start(btn,False, 0)
        btn.connect("clicked", evnt)
        if self.lshow:
            btn.lshow()
        return btn

    def show(self):
        self.div.show()
        for btn in self.tabs:
            btn.show()
        self.lshow=True

    def getDiv(self):
        return self.div

class MainWindow(threading.Thread):

    def __init__(self, width, height):
        threading.Thread.__init__(self)
        self.width=width
        self.height=height
        self.mainwindow=gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.servers = []
        self.clients = []
        self.tablist = None
        self.ActiveItem = None
        self.MainBox = None
        self.run()

    def delete_event(self, widget, event, data=None):
        print "delete event occurred"
        return False

    def destroy(self, widget, data=None):
        gtk.main_quit()

    def run(self):
        self.tablist = TabBox()
        srv = self.tablist.add("MarvinServer", lambda w: self.showServerTab("MarvinServer"))
        srv = self.tablist.add("DeviceServer", lambda w: self.showServerTab("DeviceServer"))

        self.mainwindow.connect("delete_event", self.delete_event)
        self.mainwindow.connect("destroy", self.destroy)
        self.jepp()

    def jepp(self):
        self.MainBox = gtk.VBox(False,0)

        self.MainBox.pack_start(self.tablist.getDiv(), False, False, 0)
        self.tablist.show()

        QuitButton = gtk.Button("Quit")
        QuitButton.connect("clicked", lambda w: gtk.main_quit())
        self.MainBox.pack_end(QuitButton, False, False, 0)
        QuitButton.show()

        self.mainwindow.add(self.MainBox)
        self.MainBox.show()
        self.mainwindow.show_all()
        self.mainwindow.maximize()
        self.initServerConnections()
        gtk.main()

    def initServerConnections(self):
        self.servers.append(ServerTab("MarvinServer"))
        self.servers.append(ServerTab("DeviceServer"))

    def show(self):
        for srv in self.servers:
            srv.show()
        for cli in self.clients:
            cli.show()
        if self.tablist:
            self.tablist.show()
        self.mainwindow.show()

    def showServerTab(self, btn):
        for srv in self.servers:
            if srv.name == btn:
                self.showActiveItem(srv.getDiv())

    def showActiveItem(self, new):
        if new and new <> self.ActiveItem:
            if self.ActiveItem:
                self.MainBox.remove(self.ActiveItem)
            self.ActiveItem = new
            self.MainBox.add(self.ActiveItem)
            self.MainBox.pack_end(self.ActiveItem, False, False, 0)

if __name__ == "__main__":
    win = MainWindow(500,500)
