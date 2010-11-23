#!/usr/bin/env python
#coding=utf8


import pygtk
pygtk.require('2.0')
import gtk
import pango
import threading
import server
import loggerGtk
import logger
import time
import gnomecanvas
import map
import ServerControl
import callback as cb
import gtk.gdk as gdk
gtk.gdk.threads_init()

MARSRV = "MarvinServer"
DEVSRV = "DeviceServer"

guiinstance = None

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
        self.logger = loggerGtk.logger(self.textBuffer)

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
        if name == MARSRV:
            self.sc = ServerControl.ServerControl(name, ServerControl.SERVERTYPE_MARVINSRV)
        else:
            self.sc = ServerControl.ServerControl(name, ServerControl.SERVERTYPE_DEVICESRV)
        self.sc.setLogger(self.logger)
        self.sc.cbl["onRunning"].add(cb.CallbackCall(self.onServerRunning))
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
        
    def onServerRunning(self, attributes):
        if self.name == MARSRV:
            self.sc.server.cbl["onNewClientContainer"].add(cb.CallbackCall(guiinstance.addClientContainer))
        

class ClientTabPage(TabPage):

    def __init__(self, name, clientContainer):
        TabPage.__init__(self, name)

        # start stop buttons for toolbar
        self.btndisco = gtk.Button("Disconnect")
        self.btndisco.connect("clicked", lambda w: self.disconnect())
        self.btndel = gtk.Button("Delete")
        self.btndel.connect("clicked", lambda w: self.delete())

        self.mapvis = MapVisual(clientContainer.map, 200, 200)
        #self.mapvis = MapVisual(None, 200, 200)

        self.toolbar.pack_start(self.btndisco, False, 0)
        self.toolbar.pack_start(self.btndel, False, 0)

        self.mainWidget.resize(1,2)
        self.mainWidget.attach(self.mapvis.getDiv(), 1,2,0,1, 0, 0, 0, 0)

        #self.mapvis.run()
        self.mapvis.width 

        self.mainWidget.show_all()
        self.clientContainer = clientContainer
        self.clientConnection = clientContainer.clientConnection
        self.clientContainer.cbMapRefresh = self.mapvisRefresh
        self.clientConnection.setLogger(self.logger)

    def disconnect(self):
        if self.clientConnection:
            self.clientConnection.disconnect(True)

    def close(self):
        if self.clientConnection and self.clientContainer:
            self.clientContainer.shutdown()

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

    def mapvisRefresh(self):
        self.mapvis.update()

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
            self.map.borders.add(map.Vector(map.Point(-20,-20), map.Point(0,40)))
            self.map.borders.add(map.Vector(map.Point(-20,20), map.Point(40,0)))
            self.map.borders.add(map.Vector(map.Point(20,20), map.Point(0,-40)))
            self.map.borders.add(map.Vector(map.Point(20,-20), map.Point(-40,0)))
            """
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
            """

    def getDiv(self):
        return self.area

    def show(self):
        self.update()

    def update(self, arg1="", arg2="", arg3="", arg4="", arg5="", user_data=""):
        print "MapVisual update"
        minx = miny = maxx = maxy = xoffset = yoffset = 0
        drw = self.area.root()

        print "rect dimmensions: w: " + str(self.width) + " h: " + str(self.height)

        drw.add("GnomeCanvasRect",
                fill_color='black',
                x1=0,
                x2=self.width,
                y1=0,
                y2=self.height)

        for vec in self.map.borders.getAllBorders():
            sp=vec.getStartPoint()
            ep=vec.getEndPoint()
            
            # calc bbox
            # x
            if sp.x < ep.x:
                if minx > sp.x:
                    minx = sp.x
            else:
                if minx > ep.x:
                    minx = ep.x

            if sp.x > ep.x:
                if maxx < sp.x:
                    maxx = sp.x
            else:
                if maxx < ep.x:
                    maxx = ep.x

            # y
            if sp.y < ep.y:
                if miny > sp.y:
                    miny = sp.y
            else:
                if miny > ep.y:
                    miny = ep.y

            if sp.y > ep.y:
                if maxy < sp.y:
                    maxy = sp.y
            else:
                if maxy < ep.y:
                    maxy = ep.y

        ratiox = ((maxx - minx) / (self.width))
        ratioy = ((maxy - miny) / (self.height))

        print "ratiox: " + str(ratiox)
        print "ratioy: " + str(ratioy)
        
        if ratiox > ratioy:
            ratioy = ratiox;
        else:
            ratiox = ratioy;
        
        if minx < 0:
            xoffset = (minx / ratiox)*-1
        if miny < 0:
            yoffset = (miny / ratioy)*-1
            
        count = 0
        colors = ["red","blue", "yellow"]
        
        print "minx: " + str(minx)
        print "maxx: " + str(maxx)
        print "diff: " + str(maxx - minx)
        print "miny: " + str(miny)
        print "maxy: " + str(maxy)
        print "diff: " + str(maxy - miny)
        print "ratiox: " + str(ratiox)
        print "ratioy: " + str(ratioy)
        # avoid zero deivision
        if ratiox == 0 or ratioy == 0:
            print "avoid zero division"
            return;

        count = 0
        
        for vec in self.map.borders.getAllBorders():

            ep=vec.getEndPoint()
            print "1: x1: " + str(vec.point.x) + ", y1: " + str(vec.point.y) + ", x2: " + str(ep.x) + ", y2: " + str(ep.y) + ", color: " + colors[count]
            

            x1 = ((vec.point.x / ratiox) + xoffset )
            x2 = (ep.x / ratiox) + xoffset
            y1 = (vec.point.y / ratioy) + yoffset
            y2 = (ep.y / ratioy) + yoffset
                
            print "2: x1: " + str(x1) + ", y1: " + str(y1) + ", x2: " + str(x2) + ", y2: " + str(y2) + ", color: " + colors[count]
            drw.add("GnomeCanvasLine",
                fill_color=colors[count],
                width_units=1.0,
                points=[x1, y1, x2, y2])

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
        gtk.main_quit()

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

    def addClientContainer(self, attributes):
        print "add client"
        clientContainer = attributes["clientContainer"]
        clientConnection = clientContainer.clientConnection
        clientConnection.cbl["onExternDisconnection"].add(cb.CallbackCall(self.removeClient, {"clientConnection": clientConnection}))
        self.clients[clientConnection.getClientString()] = ClientTabPage(clientConnection.getClientString(), clientContainer)
        self.tablist.add(clientConnection.getClientString(), lambda w: self.showClientTab(clientConnection.getClientString()))
        self.tablist.div.show_all()

    def removeClient(self, attributes):
        clientConnection=attributes["clientConnection"]
        print "remove client"
        cliname = clientConnection.getClientString()
        if self.clients.has_key(cliname):
            cli = self.clients[cliname]
            self.servers[MARSRV].sc.server.removeClient(cli.clientConnection)
            del self.clients[cliname]
            if self.tablist.remove(cliname):
                self.showNearestItem()
        else:
            print "client not found"
        return True


if __name__ == "__main__":
    win = MainWindow(500,500)
    win.start()
    print "..."