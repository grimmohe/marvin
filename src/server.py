#!/usr/bin/env python
#coding=utf8

import os
import socket
import threading
import network
import map
import common
import time
import xmltemplate
import math
import logger

shellInstance = None

class ServerListener(threading.Thread):

    def __init__(self, server, cb_read):
        threading.Thread.__init__(self)
        self.listening  = 0
        self.clients = []
        self.cb_read = cb_read
        self.cb_newClient = None
        self.serverInstance=server
        self.logger = None
        self.loggerbuf = []

    def __del__(self):
        self.shellEcho("destroy ServerListener")
        self.serverInstance = None
        self.socket = None

    def bind(self, ip, port):
        self.socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        try:
            self.socket.bind((ip,port))
        except socket.error:
            return False
        self.start()
        return True

    def run(self):
        self.listening = 1
        while self.listening and self.socket:
            self.listenForConnectionRequests()
        self.shellEcho("server listening stopped")

    def listenForConnectionRequests(self):
        self.socket.listen(1)
        if self.socket:
            try:
                newClient = self.socket.accept()
                newClient = ClientConnection(self,newClient,self.cb_read)
                self.clients.append(newClient)
                if self.cb_newClient:
                    self.cb_newClient(newClient)
            except socket.error:
                self.listening = False
                return

    def serverCmd(self, cmd):
        cmd = cmd.strip()
        if cmd == 'disco':
            self.shellEcho("disconnect all clients")
            self.disconnectClients()
        elif cmd == "kill":
            self.shutdown()

    def sendFile(self, file):
        """ sending file content to first available client """
        if self.clients and self.clients[0]:
            ofile = os.open(file, os.O_RDONLY)
            rc=1
            stream = ""
            while True:
                fread = os.read(ofile, 2048)
                stream += fread
                if len(fread) > 0:
                    rc = 0
                else:
                    break
            os.close(ofile)
            if len(stream) > 0:
                if not self.clients[0].write(stream):
                    self.clients.remove(self.clients[0])
                    rc = 1
                    self.sendFile(file)
            return rc
        else:
            self.shellEcho("no client available")

    def disconnectClients(self):
        for client in self.clients:
            client.disconnect(True)
        self.clients = []

    def shutdown(self):
        #self.shellEcho("shutdown")
        self.listening = 0
        #self.shellEcho("disconnect clients")
        self.disconnectClients()
        #self.shellEcho("close socket")
        self.socketClose()
        self.shellEcho("shutdown done")

    def socketClose(self):
        if self.socket:
            try:
                self.socket.shutdown(socket.SHUT_RDWR)
                self.socket.close()
            except socket.error:
                print "socketClose failed"
                return

    def shellEcho(self, msg):
        msg = "[" + self.serverInstance.name + "] " + msg
        if self.logger:
            self.logger.log(msg)
        else:
            self.loggerbuf.append(msg)
            print "buff msg: " + msg

    def setLogger(self, logger):
        if logger:
            self.logger = logger
            for msg in self.loggerbuf:
                logger.log(msg)
            self.loggerbuf = []
            logger.log("ServerListener["+self.serverInstance.name+"] logging enabled")
        else:
            self.logger = None


class ClientConnection(network.networkConnection):

    def __init__(self, server, client, cb_read):
        network.networkConnection.__init__(self)
        self.server = server
        self.clientContainer = None
        self.clientInfo = client[1]
        self.clientStuff = client
        self.cbDataIncome = cb_read
        self.socket = client[0]
        self.start()
        self.logger = None
        self.loggerbuf = []

    def __del__(self):
        self.disconnect(True)

    def disconnect(self, withDisco):
        #self.server.shellEcho("disconnecting...")
        network.networkConnection.disconnect(self, withDisco)
        self.clientInfo = None
        if self.clientContainer:
            self.clientContainer.connection = None
            self.clientContainer = None
        if self in self.server.clients:
            self.server.clients.remove(self)
        #self.shellEcho(".. done")

    def getClientString(self):
        if self.clientInfo:
            return "[" + self.clientInfo[0] + "]"
        return "[<unknown>]"


    def shellEcho(self, msg):
        msg = self.getClientString() + " " + msg
        if self.logger:
            self.logger.log(msg)
        else:
            self.loggerbuf.append(msg)

    def setLogger(self, logger):
        self.logger = logger
        for msg in self.loggerbuf:
            logger.log(msg)
        self.logger.log("ClientConnection: logging enabled")

class Shell:

    def __init__(self):
        global shellInstance
        shellInstance = self
        self.marvinsrv = None
        self.devsrv = None
        self.exit = False
        self.tmplts = None
        self.logger = logger.logger()

    def __del__(self):
        print "destroy Shell"
        self.destroyServers()


    def run(self):
        self.processCommand("start")
        print "run Shell"
        self.awaitingCommands()

    def awaitingCommands(self):
        self.exit = False
        try:
            while not self.exit:
                cmd = raw_input("cmd#>: ")
                self.processCommand(cmd)
        except KeyboardInterrupt:
            self.exit = True
        self.processCommand("stop")

    def processCommand(self,cmd):
        if len(cmd) == 0:
            return

        cmd = cmd.replace("  "," ").strip().split(" ")
        if "sft" == cmd[0]:
            self.processCommand("sf ../doc/test.xml")
        if "sfx" == cmd[0]:
            self.sendXmlTest( cmd[1], cmd[2] )
        elif "sf" == cmd[0]:
            print "sending file: ", cmd[1]
            if self.marvinsrv.srvlis.sendFile(cmd[1]) == 0:
                print "send ok"
            else:
                print "send failed"
        elif "echo" == cmd[0]:
            print ' '.join(cmd)
        elif "exit" == cmd[0]:
            self.exit = True
        elif "start" == cmd[0]:
            self.runServers()
        elif "stop" == cmd[0]:
            self.destroyServers()
        elif "srv" == cmd[0]:
            if self.marvinsrv:
                self.marvinsrv.srvlis.serverCmd(cmd[1])
        elif "dev" == cmd[0]:
            if self.devsrv:
                self.devsrv.srvlis.serverCmd(cmd[1])
        elif "help" == cmd[0]:
            print "command unkown: ",cmd[0]
            print "sf <file>"
            print "echo <text>"
            print "start|stop (a server instance)"
            print "srv|dev disco|kill"
            print "help"

    def closeCmdLine(self):
        self.processCommand("echo close Shell")

    def destroyServers(self):
        if self.marvinsrv:
            self.marvinsrv.shutdown()
        self.marvinsrv = None
        if self.devsrv:
            self.devsrv.srvlis.shutdown()
        self.devsrv = None

    def runServers(self):
        if not self.marvinsrv:
            self.marvinsrv = MarvinServer()
            self.runServer(self.marvinsrv, 50)
        if not self.devsrv:
            self.devsrv = DeviceServer()
            self.runServer(self.devsrv, 50)

    def runServer(self, srv, maxTries):
        curTry = 0
        srv.setLogger(self.logger)
        while curTry <= maxTries:
            print "try to run " + srv.name + " (" + str(curTry) + "/" + str(maxTries) + ")"
            if srv.run():
                return True
            curTry += 1
            time.sleep(5.0)
        return False

    def sendXmlTest(self, one, two):
        if not self.tmplts:
            self.tmplts = xmltemplate.TemplateList()
        tmplt = self.tmplts.lookup("erkunde-gerichtet.xml")
        if tmplt:
            tmplt.varlist.lookup("$base-sensor").value = one
            tmplt.varlist.lookup("$opposite-sensor").value = two
            tmplt.varlist.lookup("$id").value = "1"
            self.marvinsrv.srvlis.clients[0].write('<what-to-do>' + tmplt.fill() + '</what-to-do>')
            #print('<what-to-do><assignment id="1" start="head:move=down"><event ifarg1="head:position" ifcompare="e" ifarg2="100" then="" final="true"/></assignment>' + tmplt.fill() + '</what-to-do>')

class Server:

    def __init__(self, name, ip, port, cb_read):
        self.name = name
        self.ip = ip
        self.port = port
        self.srvlis = ServerListener(self, cb_read)

    def __del__(self):
        self.srvlis = None

    def broadcast(self,data,exceptConnections):
        for client in self.srvlis.clients:
            if not client in exceptConnections:
                if not client.write(data):
                    # clientconnection is invalid, removeit
                    self.srvlis.clients.remove(client)
                    client = None

    def run(self):
        if self.srvlis:
            return self.srvlis.bind(self.ip, self.port)
        return False

    def shutdown(self):
        if self.srvlis:
            self.srvlis.shutdown()
            self.srvlis = None
            
    def setLogger(self, logger):
        self.srvlis.setLogger(logger)

class ClientContainer(threading.Thread):

    def __init__(self):
        print "new ClientContainer"
        threading.Thread.__init__(self)
        self.position = map.Position()
        self.map = map.Map()
        self.devs = {}
        self.connection = None
        self.actionlogData = ""
        self.actionlogNew = threading.Event()
        self.stop = False
        self.x = 0
        self.y = 0
        self.start()

    def assimilateActions(self, actionlog):
        """ turn the cliens action log into a map and if send, get some other infos """
        for action in actionlog.actions:
            # contains action and value
            dev, key = action.action.split(":")
            dev = dev.lower()
            key = key.lower()
            if dev == "engine" and self.devs.has_key(dev):
                if key == "turned":
                    self.position.orientation += action.value
                    for dev in self.devs.values():
                        if dev.has_key("touch"):
                            dev["touch"] = False
                elif key == "distance" and self.devs[dev].has_key(key):
                    new_x = self.x + math.sin(math.radians(self.position.orientation)) * action.value
                    new_y = self.y + math.cos(math.radians(self.position.orientation)) * action.value
                    v_start = self.devs[dev]["dimension"].copy(map.Point(self.position.point.x, self.position.point.y),
                                                               self.position.orientation)
                    v_end = self.devs[dev]["dimension"].copy(map.Point(new_x, new_y), self.position.orientation)
                    for dev in self.devs:
                        if dev.has_key("touch") and dev["touch"]:
                            # sensor at start position
                            self.map.borders.add(v_start)
                            # sensor on end position
                            self.map.borders.add(v_end)
                            # point 1 start to end
                            self.map.borders.add(map.Vector().combine(v_start, v_end, map.Vector.START_POINT))
                            # point 2 start to end
                            self.map.borders.add(map.Vector().combine(v_start, v_end, map.Vector.END_POINT))
                        if dev.has_key("position") and dev["position"]:
                            self.map.addArea(v_start.getStartPoint(), v_start.getEndPoint(), v_end.getStartPoint())
            else:
                if not self.devs.has_key(dev):
                    self.devs[dev] = {}
                self.devs[dev][key] = action.value
                if key == "distance":
                    self.devs[dev]["touch"] = (action.value < 1.0)
                    if self.devs[dev]["touch"]:
                        sensorOffset = None
                        if self.devs[dev].has_key("orientation"):
                            sensorOffset = self.devs[dev]["orientation"]
                        self.map.borders.add(self.devs[dev]["dimension"].copy(map.Point(self.position.point.x,
                                                                                        self.position.point.y),
                                                                              self.position.orientation,
                                                                              sensorOffset))
                elif key == "dimension":
                    x, y, size_x, size_y = action.value.split(";")
                    self.devs[dev][key] = map.Vector(map.Point(x, y), map.Point(size_x, size_y))
                elif key == "orientation":
                    size_x, size_y = action.value.split(";")
                    self.devs[dev][key] = map.Vector(map.Point(0, 0), map.Point(size_x, size_y))
                elif key in ("radius", "position"):
                    self.devs[dev][key] = float(action.value)
        self.map.merge()

    def discover(self):
        """ discover new borders """
        if self.devs.has_key("self") and self.devs["self"].has_key("radius"):
            loose = self.map.borders.getLooseEnds(self.position)
            if loose and len(loose):
                loose = loose[0]
                vlen = loose.len()
                bmulti = min(vlen, self.devs["self"]["radius"]) / vlen
                self.map.addWaypoint(map.WayPoint(loose.point.x + loose.size.x * bmulti,
                                                  loose.point.y + loose.size.y * bmulti,
                                                  map.WayPoint.WP_FAST | map.WayPoint.WP_DISCOVER,
                                                  loose))
            elif self.map.borders.count() == 0:
                self.map.addWaypoint(map.WayPoint(self.position.point.x, self.position.point.y, map.WayPoint.WP_DISCOVER))
        else:
            self.connection.shellEcho("try to discover, but no \"radius\" item found" )

    def getSensorList(self, extended=False):
        sensors = []
        for devname in self.devs:
            if self.devs[devname].has_key("dimension") and self.devs[devname].has_key("distance"):
                if extended: os = self.devs[devname]["distance"]
                else: os = 0
                s = self.devs[devname]["dimension"].copy(offset=os)
                s.name = devname
                sensors.append(s)
        return sensors

    def handlePanicEvents(self):
        """ in case the batterie is low or other stuff, handle that """
        if not self.devs.has_key("self") or not self.devs["self"].has_key("raduis"):
            pass
            #TODO: Oh, panic!(TM)

    def run(self):
        print "start run"
        while not self.stop:
            print "start wait"
            self.actionlogNew.clear()
            self.actionlogNew.wait()
            print "done wait"
            if not self.stop and self.actionlogData:
                print "data:"
                print self.actionlogData
                actionlog = common.Actionlog()
                try:
                    actionlog.readXml(self.actionlogData)
                except:
                    print "no valid xml data?"
                self.assimilateActions(actionlog)
                self.handlePanicEvents()
                if not self.map.routeIsSet():
                    self.discover()
                if not self.map.routeIsSet():
                    self.fill()
                self.sendAssignments()

    def fill(self):
        """ yea... grimm, what to do here? self.map has no route, now FILLLLLL it! """
        pass

    def sendAssignments(self):
        """
        send assignments in a packed format back to our waiting client.
        there, xml-templates will be filled and executed.
        """
        pos = map.Position(map.Point(self.position.point.x, self.position.point.y), self.position.orientation)
        router = map.Router(self.devs["self"]["radius"])
        for wp in self.map.waypoints:
            if wp.duty & map.WayPoint.WP_FAST:
                router.actionRoute(pos, wp, xmltemplate.addTemplate)

            if wp.duty & map.WayPoint.WP_STRICT:
                collisions = self.map.getCollisions(pos, self.getSensorList(True), 0)
                for i in range(len(collisions)):
                    if pos.point.getDistanceTo(wp) < collisions[i][0]:
                        break
                    router.actionRoute(pos, collisions[i][2], xmltemplate.addTemplate)
                    if i < len(collisions)-1:
                        bpos = map.Position(collisions[i+1][2], pos.orientation+180)
                        bc = self.map.getCollisions(bpos, self.getSensorList(True), 0)
                        if len(bc) and pos.point.getDistanceTo(wp) < bc[0][0]:
                            router.actionRoute(pos, bc[0][2], xmltemplate.addTemplate)

            if wp.duty & map.WayPoint.WP_DISCOVER:
                router.actionDiscover(pos, wp.attachment, cb_getSensorList=self.getSensorList, cb_addAction=xmltemplate.addTemplate)

        self.connection.write(xmltemplate.getTransmissionData())
        self.map.clearWaypoints()
        xmltemplate.clear()

    def shutdown(self):
        if self.connection:
            self.connection.disconnect(True)
        self.connection = None
        self.actionlog = None
        # semi fire event to come out of wait state, but set stop flag before, so thread
        # is killed
        self.stop = True
        if self.actionlogNew:
            self.actionlogNew.set()
        self.actionlogNew = None
        self.map = None

class MarvinServer(Server):

    def __init__(self):
        Server.__init__(self, "MarvinServer",'127.0.0.1',29875, self.ClientReceiving)
        self.srvlis.cb_newClient=self.addClient
        self.cb_addClient = None
        self.clients = []

    def __del__(self):
        self.shutdown()

    def ClientReceiving(self, connection, data):
        #connection.shellEcho(" received: " + data)
        client = None
        for c in self.clients:
            if c.connection == connection:
                client = c
        if client:
            client.actionlogData=data
            client.actionlogNew.set()
        else:
            print "no suitable client found"

    def addClient(self, clientConnection):
        clientConnection.clientContainer=ClientContainer()
        clientConnection.clientContainer.connection = clientConnection
        self.clients.append(clientConnection.clientContainer)
        if self.cb_addClient:
            self.cb_addClient(clientConnection)
        self.srvlis.shellEcho("client added")

    def removeClient(self, clientConnection):
        for cli in self.clients:
            if cli.connection == clientConnection:
                cli.shutdown()
                self.clients.remove(cli)

    def shutdown(self):
        for client in self.clients:
            client.shutdown()
            del client
            client=None
        self.clients=[]
        Server.shutdown(self)

class DeviceServer(Server):

    def __init__(self):
        Server.__init__(self, "DeviceServer",'127.0.0.1',29874, self.ClientReceiving)

    def ClientReceiving(self, connection, data):
        self.broadcast(data, [connection])


if __name__ == '__main__':
    Shell()
    shellInstance.run()
