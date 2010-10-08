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
import gnomecanvas
import map
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
        self.server = None

    def run(self):
        self.prints("running..")
        self.ServerStart()
        while not self.stop:
            self.event_SwitchState.clear()
            self.event_SwitchState.wait()
            self.prints("event!")
            if self.stop:
                if self.server:
                    self.ServerStop()
                self.prints("leaving event loop")
                return
            if self.server:
                self.ServerStop()
            else:
                self.ServerStart()


    def ServerStop(self):
        self.tab.logger.log("stop server " + self.tab.name)
        if self.server:
            self.server.shutdown()
        self.server=None

    def ServerStart(self):
        self.tab.logger.log("start server " + self.tab.name)
        if not self.server:
            if self.tab.name == MARSRV:
                self.server = server.MarvinServer()
                self.server.cb_addClient = guiinstance.addClient
            if self.tab.name == DEVSRV:
                self.server = server.DeviceServer()
            self.server.srvlis.setLogger(self.tab.logger)
            if self.ServerRun(50):
                self.tab.logger.log("done (" + self.server.srvlis.name + ")")
            else:
                self.tab.logger.log("failed")


    def ServerRun(self, maxTries):
        curTry = 0
        while curTry <= maxTries:
            self.tab.logger.log( "try to run " + self.server.name + " (" + str(curTry) + "/" + str(maxTries) + ")")
            if self.server.run():
                return True
            curTry += 1
            time.sleep(5.0)
        return False

    def setStop(self, stop):
        self.stop = stop

    def isRunning(self):
        if self.server:
            return True
        return False

    def destroy(self):
        self.prints("destroy")
        if self.server:
            self.server.srvlis.setLogger(None)
        self.stop = True
        self.event_SwitchState.set()
        self.prints("done..")

    def prints(self, msg):
         print "ServerControl " + self.name + ": " + msg

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

        #wrap words in textinput
        self.textView.set_wrap_mode(gtk.WRAP_WORD)

        # join text and scrollable window
        self.scrollableWindow.add(self.textView)

        self.toolbar = gtk.HBox(False, 0)

        self.mainWidget.attach(self.scrollableWindow, 0,1,0,1)
        self.mainWidget.attach(self.toolbar, 0,1,1,2,0,0,0,0)

        # new textbuffer logger
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
        self.sc = ServerControl(self)
        self.sc.start()

    def serverStop(self):
        if self.sc.isRunning():
            self.sc.event_SwitchState.set()

    def serverStart(self):
        if not self.sc.isRunning():
            self.sc.event_SwitchState.set()

    def close(self):
        print "ServerTabPage closing"
        if self.sc:
            self.sc.destroy()
        self.sc = None
        self.logger = None
        self.logger = logger.logger()
        print "ServerTabPage closed"

class ClientTabPage(TabPage):

    def __init__(self, name, clientConnection):
        TabPage.__init__(self, name)

        # start stop buttons for toolbar
        self.btndisco = gtk.Button("Disconnect")
        self.btndisco.connect("clicked", lambda w: self.disconnect())
        self.btndel = gtk.Button("Delete")
        self.btndel.connect("clicked", lambda w: self.delete())

        self.mapvis = MapVisual(clientConnection.clientContainer.map, 200, 200)
        #self.mapvis = MapVisual(None, 200, 200)

        self.toolbar.pack_start(self.btndisco, False, 0)
        self.toolbar.pack_start(self.btndel, False, 0)

        self.mainWidget.resize(1,2)
        self.mainWidget.attach(self.mapvis.getDiv(), 1,2,0,1, 0, 0, 0, 0)

        #self.mapvis.run()
        self.mapvis.width 

        self.mainWidget.show_all()
        self.clientConnection = clientConnection
        self.clientConnection.setLogger(self.logger)

    def disconnect(self):
        if self.clientConnection:
            self.clientConnection.disconnect(True)

    def close(self):
        if self.clientConnection and self.clientConnection.clientContainer:
            self.clientConnection.clientContainer.shutdown()

    def delete(self):
        if not guiinstance.removeClient(self.clientConnection):
            print "remove of " + self.name + " failed"
            return False
        self.disconnect()
        self.close()
        return True

    def getDiv(self, parent=None):
        if parent:
            self.mapvis.update()
        return self.mainWidget


class MapVisual:

    def __init__(self, _map, height, width):
        self.area = gnomecanvas.Canvas(aa=True)
        self.map = _map
        self.height = height
        self.width = width
        self.area.set_size_request(height, width)
        self.area.connect("draw-background", self.update)
        if not self.map:
            """ some rtesting stuff ifnot map is set """
            print "using test map"
            self.map = map.Map()
            self.map.borders.add(map.Vector(map.Point(0,0), map.Point(0,10)))
            self.map.borders.add(map.Vector(map.Point(0,10), map.Point(10,10)))
            self.map.borders.add(map.Vector(map.Point(10,10), map.Point(10,0)))
            self.map.borders.add(map.Vector(map.Point(0,0), map.Point(10,5)))
            #T
            self.map.borders.add(map.Vector(map.Point(0.5,3), map.Point(1.5,3)))
            self.map.borders.add(map.Vector(map.Point(1,3), map.Point(1,4)))
            #E
            self.map.borders.add(map.Vector(map.Point(2,3), map.Point(3,3)))
            self.map.borders.add(map.Vector(map.Point(2,3.5), map.Point(3,3.5)))
            self.map.borders.add(map.Vector(map.Point(2,4), map.Point(3,4)))
            self.map.borders.add(map.Vector(map.Point(2,3), map.Point(2,4)))
            #S
            self.map.borders.add(map.Vector(map.Point(4,3), map.Point(5,3)))
            self.map.borders.add(map.Vector(map.Point(4,3), map.Point(4,3.5)))
            self.map.borders.add(map.Vector(map.Point(4,3.5), map.Point(5,3.5)))
            self.map.borders.add(map.Vector(map.Point(5,3.5), map.Point(5,4)))
            self.map.borders.add(map.Vector(map.Point(4,4), map.Point(5,4)))
            #T
            self.map.borders.add(map.Vector(map.Point(5.5,3), map.Point(6.5,3)))
            self.map.borders.add(map.Vector(map.Point(6,3), map.Point(6,4)))


    def getDiv(self):
        return self.area

    def show(self):
        self.update()

    def update(self, arg1="", arg2="", arg3="", arg4="", arg5="", user_data=""):
        print "MapVisual update"
        minx = miny = maxx = maxy = 0
        drw = self.area.root()

        print "rect dimmensions: w: " + str(self.width) + " h: " + str(self.height)

        drw.add("GnomeCanvasRect",
                fill_color='black',
                x1=-50,
                x2=self.width,
                y1=-50,
                y2=self.height)


        for vec in self.map.borders.getAllBorders():
            if minx > vec.point.x:
                minx = vec.point.x
            if miny > vec.point.y:
                miny = vec.point.y

            if maxx < vec.size.x:
                maxx = vec.size.x
            if maxy < vec.size.y:
                maxy = vec.size.y

        ratiox = ((maxx - minx) / self.width)
        ratioy = ((maxy - miny) / self.height)
        count = 0
        colors = ["red","blue", "yellow"]
        for vec in self.map.borders.getAllBorders():

            x1 = (vec.point.x / ratiox) - 50
            x2 = (vec.size.x / ratiox) - 50
            y1 = (vec.point.y / ratioy) - 50
            y2 = (vec.size.y / ratioy) - 50

            print "x1: " + str(x1) + ", y1: " + str(y1) + ",x2: " + str(x2) + ", y2: " + str(y2) + ", color: " + colors[count]
            drw.add("GnomeCanvasLine",
                fill_color=colors[count],
                width_units=1.0,
                points=[x1,
                        y1,
                        x2,
                        y2])

            if count == 2:
                count = 0
            else:
                count += 1

class TabBox:

    def __init__(self):
        self.tabs = {}
        self.div = gtk.HBox()
        self.lshow = False

    def add(self, name, evnt):
        btn = gtk.Button(name)
        self.tabs[name] = btn
        self.div.pack_start(btn,False, 0)
        btn.connect("clicked", evnt)
        if self.lshow:
            btn.show()
        return btn

    def remove(self, name):
        self.div.remove(self.tabs[name])
        del self.tabs[name]
        self.div.show_all()
        return True

    def show(self):
        self.div.show_all()
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
        self.mainwindow=None
        self.servers = {}
        self.clients = {}
        self.tablist = None
        self.ActiveItem = None
        self.MainBox = None

    def fromGtk_delete(self, widget, event, data=None):
        self.destroy()
        return False

    def fromGtk_destroy(self, widget):
        self.destroy()

    def destroy(self):
        for cli in self.clients.values():
            cli.close()
        self.clients = {}
        for srv in self.servers.values():
            srv.close()
        self.servers = {}


    def quit(self, widget, data=None):
        self.destroy()
        gtk.main_quit()

    def run(self):
        global guiinstance
        print "run thread " + self.name + "(MainWindow)"

        self.buildMainWindow()
        self.buildTabList()
        self.buildMainBox()
        self.initServerConnections()

        # show mainwindow
        self.mainwindow.show_all()
        #self.mainwindow.maximize()

        self.showNearestItem()

        gtk.main()

        guiinstance = None

    def buildMainWindow(self):
        self.mainwindow = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.mainwindow.connect("delete_event", self.fromGtk_delete)
        self.mainwindow.connect("destroy", self.fromGtk_destroy)

    def buildTabList(self):
        self.tablist = TabBox()
        self.tablist.add(MARSRV, lambda w: self.showServerTab(MARSRV))
        self.tablist.add(DEVSRV, lambda w: self.showServerTab(DEVSRV))

    def buildMainBox(self):
        self.MainBox = gtk.VBox(False,0)
        self.MainBox.pack_start(self.tablist.getDiv(), False, False, 0)

        # big quit button
        QuitButton = gtk.Button("Quit")
        QuitButton.connect("clicked", lambda w: self.quit(None))
        self.MainBox.pack_end(QuitButton, False, False, 0)
        self.mainwindow.add(self.MainBox)

    def initServerConnections(self):
        self.servers[MARSRV] = ServerTabPage(MARSRV)
        self.servers[DEVSRV] = ServerTabPage(DEVSRV)

    def showServerTab(self, btn):
        self.showActiveItem(self.servers[btn].getDiv())

    def showClientTab(self, btn):
        self.showActiveItem(self.clients[btn].getDiv(self.MainBox.window))

    def showActiveItem(self, new):
        if new and new <> self.ActiveItem:
            if self.ActiveItem:
                self.MainBox.remove(self.ActiveItem)
            self.ActiveItem = new
            self.MainBox.add(self.ActiveItem)

    def showNearestItem(self):
        if len(self.clients) > 0:
            self.showActiveItem(self.clients.values()[0].getDiv())
        else:
            self.showActiveItem(self.servers.values()[0].getDiv())

    def addClient(self, clientConnection):
        print "add client"
        clientConnection.cbDisconnect = lambda w: self.removeClient(clientConnection) 
        self.clients[clientConnection.getClientString()] = ClientTabPage(clientConnection.getClientString(), clientConnection)
        self.tablist.add(clientConnection.getClientString(), lambda w: self.showClientTab(clientConnection.getClientString()))
        self.tablist.div.show_all()

    def removeClient(self, clientConnection):
        print "remove client"
        cliname = clientConnection.getClientString()
        cli = self.clients[cliname]
        self.servers[MARSRV].sc.server.removeClient(cli.clientConnection)
        del self.clients[cliname]
        if self.tablist.remove(cliname):
            self.showNearestItem()
        return True


if __name__ == "__main__":
    win = MainWindow(500,500)
    win.start()
    print "..."