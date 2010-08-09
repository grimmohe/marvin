#!/usr/bin/env python
#coding=utf8


import pygtk
pygtk.require('2.0')
import gtk
import pango
import threading

class ServerTab:

    def __init__(self, server, name):

        self.div = gtk.VBox(False, 0)
        self.widgetTable = gtk.Table(1,2,False)

        self.editor = gtk.TextView()
        self.textbf = self.editor.get_buffer()
        self.sw = gtk.ScrolledWindow()
        self.sw.set_policy(gtk.POLICY_AUTOMATIC,gtk.POLICY_AUTOMATIC)
        self.editor.set_wrap_mode(gtk.WRAP_WORD)
        self.sw.add(self.editor)
        self.textbf.insert_at_cursor("narf\ntest")

        self.btnstop = gtk.Button("Stop")
        self.btnstart = gtk.Button("Start")

        self.tooldiv = gtk.HBox(False, 0)
        self.tooldiv.pack_start(self.btnstart, False, 0)
        self.tooldiv.pack_start(self.btnstop, False, 0)

        tooldivalign = gtk.Alignment(1,0,0,0)
        tooldivalign.add(self.tooldiv)

        self.widgetTable.attach(self.sw, 0,1,0,1)
        self.widgetTable.attach(tooldivalign, 0,1,1,2)

        self.div.pack_end(self.widgetTable, False, False, 0)

        self.editor.show()
        self.btnstop.show()
        self.btnstart.show()
        self.widgetTable.show()
        self.sw.show()
        self.server = server
        self.name = name

    def ServerStop(self):
        self.server.shutdown()
        self.server=None

    def ServerStart(self):
        pass

    def getDiv(self):
        return self.div

class TabBox:

    def __init__(self):
        self.tabs = []
        self.div = gtk.HBox()
        self.lshow = False

    def add(self, name):
        btn = gtk.Button(name)
        self.tabs.append(btn)
        self.div.pack_start(btn,False, 0)
        if self.lshow:
            btn.lshow()

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

        srv = ServerTab(None, "MarvinSrv")
        self.servers.append(srv)
        self.ActiveItem = srv.getDiv()
        #self.container.add(srv.getDiv())
        #srv = ServerTab(None, "DeviceSrv")
        #self.servers.append(srv)
        #self.container.add(srv.getDiv())
        #self.tablist = TabBox()
        self.tablist.add("MarvinServer")
        self.tablist.add("DeviceServer")
        self.mainwindow.connect("delete_event", self.delete_event)
        self.mainwindow.connect("destroy", self.destroy)


        self.jepp()


    def jepp(self):
        self.MainBox = gtk.VBox(False,0)

        self.MainBox.pack_start(self.tablist.getDiv(), False, False, 0)
        self.tablist.show()

        ContentBox = self.ActiveItem
        self.MainBox.pack_start(ContentBox, False, False, 0)
        ContentBox.show()

        QuitButton = gtk.Button("Quit")
        QuitButton.connect("clicked", lambda w: gtk.main_quit())
        self.MainBox.pack_end(QuitButton, False, False, 0)
        QuitButton.show()

        QuitButton = gtk.Button("Test")
        QuitButton.connect("clicked", self.test)
        self.MainBox.pack_end(QuitButton, False, False, 0)
        QuitButton.show()

        self.mainwindow.add(self.MainBox)
        self.MainBox.show()
        self.mainwindow.show_all()
        self.mainwindow.maximize()
        gtk.main()

    def show(self):
        for srv in self.servers:
            srv.show()
        for cli in self.clients:
            cli.show()
        if self.tablist:
            self.tablist.show()
        self.mainwindow.show()

    def test(self):
        QuitButton = gtk.Button("Test1")
        QuitButton.connect("clicked", self.test)
        self.MainBox.add(QuitButton)
        self.MainBox.pack_end(QuitButton, False, False, 0)
        self.mainwindow.show_all()

if __name__ == "__main__":
    win = MainWindow(500,500)
