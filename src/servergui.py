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
import math
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
        #self.mainWidget.attach(self.mapvis, 1,2,0,1, 0, 0, 0, 0)
        self.mainWidget.attach(self.mapvis, 1,2,0,1, gtk.FILL, gtk.FILL, 0, 0)

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
        #self.mapvis.expose()
        gtk.Widget.queue_draw(self.mapvis)

class BBox:
    
    def __init__(self):
        self.minx = 0
        self.miny = 0
        self.maxx = 0
        self.maxy = 0
        
    def addPoint(self, x, y):
        if self.minx > x:
            self.minx = x

        if self.maxx < x:
            self.maxx = x
    
        if self.miny > y:
            self.miny = y

        if self.maxy < y:
            self.maxy = y


class MapVisual(gtk.DrawingArea):

    def __init__(self, _map, height, width):
        gtk.DrawingArea.__init__(self)
        self.connect("expose_event", self.expose)
        self.map = _map
        self.height = height
        self.width = width
        self.set_size_request(height, width)
        self.context = None
        self.lock=False
        
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
        
    def expose(self, widget, event):
        print "expose"
        self.context = widget.window.cairo_create()
        self.context.rectangle(event.area.x, event.area.y,
                       event.area.width, event.area.height)
        
        self.context.clip()
        
        self.draw(self.context)
        
        return False

    def draw(self, context):
        print "draw"
        rect = self.get_allocation()
        
        x=0
        y=0
        width=rect.width
        height=rect.height
        print x, y, width, height
        
        self.update()

    def show(self):
        self.update()

    def update(self, arg1="", arg2="", arg3="", arg4="", arg5="", user_data=""):

        if not self.context or self.lock:
            print "silent return"
            return
        
        self.lock=True
        print "MapVisual update"
        minx = miny = maxx = maxy = xoffset = yoffset = 0
        #self.drw = self.area.root()
        self.ratiox=0
        self.ratioy=0
        self.offsetx=0
        self.offsety=0

        print "rect dimmensions: w: " + str(self.width) + " h: " + str(self.height)

        #for item in self.drw.item_list:
        #    self.drw.item_list.remove(item)
            
        """        
        self.drw.add("GnomeCanvasRect",
                fill_color='black',
                x1=0,
                x2=self.width,
                y1=0,
                y2=self.height)
        """
        
        self.context.new_path();
        self.context.rectangle(0,0,self.width, self.height) 
        self.context.close_path();
        
        self.context.set_source_rgb(0, 0, 0)
        self.context.fill_preserve()
        self.context.set_source_rgb(0, 0, 0)
        self.context.stroke()
                
        bbox = BBox() 

        for vec in self.map.borders.getAllBorders():
            sp=vec.getStartPoint()
            ep=vec.getEndPoint()
            
            bbox.addPoint(sp.x, sp.y)
            bbox.addPoint(ep.x, ep.y)

        for area in self.map.areas:
            bbox.addPoint(area.p1.x, area.p1.y)
            bbox.addPoint(area.p2.x, area.p2.y)
            bbox.addPoint(area.p3.x, area.p3.y)

        minx = bbox.minx
        miny = bbox.miny
        maxx = bbox.maxx
        maxy = bbox.maxy
        
        self.ratiox = ((maxx - minx) / (self.width))
        self.ratioy = ((maxy - miny) / (self.height))

        print "ratiox: " + str(self.ratiox)
        print "ratioy: " + str(self.ratioy)
        
        if self.ratiox > self.ratioy:
            self.ratioy = self.ratiox;
        else:
            self.ratiox = self.ratioy;
        
        if minx < 0:
            self.offsetx = (minx / self.ratiox)*-1
        if miny < 0:
            self.offsety = (miny / self.ratioy)*-1
            
        count = 0
        colors = ["red","blue", "green"]
        
        print "minx: " + str(minx)
        print "maxx: " + str(maxx)
        print "diff: " + str(maxx - minx)
        print "miny: " + str(miny)
        print "maxy: " + str(maxy)
        print "diff: " + str(maxy - miny)
        print "ratiox: " + str(self.ratiox)
        print "ratioy: " + str(self.ratioy)
        # avoid zero deivision
        if self.ratiox == 0 or self.ratioy == 0:
            print "avoid zero division"
            self.lock=False
            return;

        count = 0

        print "draw borders"
        
        for vec in self.map.borders.getAllBorders():
            ep=vec.getEndPoint()
            self.drawLine(vec.point.x, vec.point.y, ep.x, ep.y,0)
            if count == 2:
                count = 0
            else:
                count += 1

        print "draw areas"

        for area in self.map.areas:
            ep=vec.getEndPoint()
            self.drawLine(area.p1.x, area.p1.y, area.p2.x, area.p2.y, 1)
            self.drawLine(area.p2.x, area.p2.y, area.p3.x, area.p3.y, 1)
            self.drawLine(area.p3.x, area.p3.y, area.p1.x, area.p1.y, 1)
            if count == 2:
                count = 0
            else:
                count += 1 
        
        print "done printing"    
        self.lock=False           
                
    def drawLine(self, x1, y1, x2, y2, coleur):
        print "1: x1: " + str(x1) + ", y1: " + str(y1) + ", x2: " + str(x2) + ", y2: " + str(y2)
        
        x1 = (x1 / self.ratiox) + self.offsetx
        x2 = (x2 / self.ratiox) + self.offsetx
        y1 = (y1 / self.ratioy) + self.offsety
        y2 = (y2 / self.ratioy) + self.offsety

        print "2: x1: " + str(x1) + ", y1: " + str(y1) + ", x2: " + str(x2) + ", y2: " + str(y2)

        if (x1 < 0 or x1 > self.width or x2 < 0 or x2 > self.width 
            or y1 < 0 or y1 > self.height or y2 < 0 or y2 > self.height):
            print "error, coord out of range"
            return
        
        """            
        item = self.drw.add("GnomeCanvasLine",
            fill_color=coleur,
            width_pixels=1,
            points=[x1, y1, x2, y2])
        
        if not item:
            print "item not valid"
        """
        
        self.context.new_path()
        self.context.move_to(int(x1),int(y1))
        self.context.line_to(int(x2),int(y2))
        self.context.close_path()
        
        if coleur == 0:
            r=0
            g=0
            b=1
        else:
            r=0
            g=1
            b=0 

        self.context.set_source_rgb(r, g, b)
        self.context.fill_preserve()
        self.context.set_source_rgb(r, g, b)
        self.context.stroke()
        
        
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