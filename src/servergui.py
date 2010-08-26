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
gtk.gdk.threads_init()

MARSRV = "MarvinServer"
DEVSRV = "DeviceServer"

guiinstance = None

class ServerControl(threading.Thread):

    def __init__(self, tab):
        threading.Thread.__init__(self)
        self.event_SwitchState = threading.Event()
        self.tab = tab
        self.stop = False

    def run(self):
        while not self.stop:
            self.event_SwitchState.clear()
            self.event_SwitchState.wait()
            if self.stop:
                return
            if self.tab.server:
                self.ServerStop()
            else:
                self.ServerStart()

    def ServerStop(self):
        self.tab.logger.log("stop server " + self.tab.name)
        if self.tab.server:
            self.tab.server.shutdown()
        self.server=None

    def ServerStart(self):
        #self.tab.logger.log("start server " + self.tab.name)
        if not self.tab.server:
            if self.tab.name == MARSRV:
                self.tab.server = server.MarvinServer()
                self.tab.server.cb_addClient = guiinstance.newClient
            if self.tab.name == DEVSRV:
                self.tab.server = server.DeviceServer()
            self.tab.server.srvlis.setLogger(self.tab.logger)
            if self.ServerRun(50):
                self.tab.logger.log("done")
            else:
                self.tab.logger.log("failed")


    def ServerRun(self, maxTries):
        curTry = 0
        while curTry <= maxTries:
            self.tab.logger.log( "try to run " + self.tab.server.name + " (" + str(curTry) + "/" + str(maxTries) + ")")
            if self.tab.server.run():
                return True
            curTry += 1
            time.sleep(5.0)
        return False

    def setStop(self, stop):
        self.stop = stop

class TabPage:

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

        self.toolbar = gtk.HBox(False, 0)

        self.mainWidget.attach(self.scrollableWindow, 0,1,0,1)
        self.mainWidget.attach(self.toolbar, 0,1,1,2,0,0,0,0)

        self.logger = logger.loggerTextBuffer(self.textBuffer)
        self.name = name

    def getDiv(self):
        return self.mainWidget

    def close(self):
        pass

class ServerTabPage(TabPage):

    def __init__(self, name):
        TabPage.__init__(self, name)

        # start stop buttons for toolbar
        self.btnstop = gtk.Button("Stop")
        self.btnstop.connect("clicked", lambda w: self.serverStop())
        self.btnstart = gtk.Button("Start")
        self.btnstart.connect("clicked", lambda w: self.serverStart())

        self.toolbar.pack_start(self.btnstart, False, 0)
        self.toolbar.pack_end(self.btnstop, False, 0)

        self.mainWidget.show_all()
        self.logger = logger.loggerTextBuffer(self.textBuffer)
        self.server = None
        self.sc = ServerControl(self)
        self.sc.start()

    def serverStop(self):
        if self.server:
            self.sc.event_SwitchState.set()

    def serverStart(self):
        if not self.server:
            self.sc.event_SwitchState.set()

    def close(self):
        if self.server:
            self.sc.setStop(True)
            self.sc.event_SwitchState.set()

class ClientTabPage(TabPage):

    def __init__(self, name, clientConnection):
        TabPage.__init__(self, name)

        # start stop buttons for toolbar
        self.btndisco = gtk.Button("Disconnect")
        self.btndisco.connect("clicked", lambda w: self.disconnect())

        self.toolbar.pack_start(self.btndisco, False, 0)

        self.mainWidget.show_all()
        self.logger = logger.loggerTextBuffer(self.textBuffer)
        self.clientConnection = clientConnection
        self.clientConnection.setLogger(self.logger)

    def disconnect(self):
        pass

    def close(self):
        if self.clientConnection:
            self.clientConnection.clientContainer.shutdown()

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
            btn.show()
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
        global guiinstance
        guiinstance = self
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
        for srv in self.servers:
            srv.close()
        for cli in self.clients:
            cli.close()
        gtk.main_quit()

    def run(self):
        self.tablist = TabBox()
        self.tablist.add(MARSRV, lambda w: self.showServerTab(MARSRV))
        self.tablist.add(DEVSRV, lambda w: self.showServerTab(DEVSRV))

        self.mainwindow.connect("delete_event", self.delete_event)
        self.mainwindow.connect("destroy", self.destroy)
        self.jepp()

    def jepp(self):
        self.MainBox = gtk.VBox(False,0)

        self.MainBox.pack_start(self.tablist.getDiv(), False, False, 0)
        self.tablist.show()

        QuitButton = gtk.Button("Quit")
        QuitButton.connect("clicked", lambda w: self.destroy(None))
        self.MainBox.pack_end(QuitButton, False, False, 0)
        QuitButton.show()

        self.mainwindow.add(self.MainBox)
        self.MainBox.show()
        self.mainwindow.show_all()
        #self.mainwindow.maximize()
        self.initServerConnections()
        gtk.main()

    def initServerConnections(self):
        self.servers.append(ServerTabPage(MARSRV))
        self.servers.append(ServerTabPage(DEVSRV))

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

    def showClientTab(self, btn):
        for cli in self.clients:
            if cli.name == btn:
                self.showActiveItem(cli.getDiv())

    def showActiveItem(self, new):
        if new and new <> self.ActiveItem:
            if self.ActiveItem:
                self.MainBox.remove(self.ActiveItem)
            self.ActiveItem = new
            self.MainBox.add(self.ActiveItem)
            self.MainBox.pack_end(self.ActiveItem, False, False, 0)

    def newClient(self, con):
        print "add client"
        self.clients.append(ClientTabPage(con.getClientString(), con))
        self.tablist.add(con.getClientString(), lambda w: self.showClientTab(con.getClientString()))
        self.tablist.div.show()

if __name__ == "__main__":
    win = MainWindow(500,500)
