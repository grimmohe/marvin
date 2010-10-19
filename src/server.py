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
import callback as cb

shellInstance = None

class ServerListener(threading.Thread):

    def __init__(self, server):
        threading.Thread.__init__(self)
        self.listening  = 0
        self.clients = []
        self.serverInstance=server
        self.logger = logger.logger()

    def __del__(self):
        self.log("destroy ServerListener")
        self.serverInstance = None
        self.socket = None

    def bind(self, ip, port):
        self.socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        try:
            self.socket.bind((ip,port))
        except IOError as (errno, strerror):
            print "I/O error({0}): {1}".format(errno, strerror)
            return False
        self.log("binded...")
        self.start()
        return True

    def run(self):
        self.listening = 1
        while self.listening and self.socket:
            self.listenForConnectionRequests()
        self.log("server listening stopped")

    def listenForConnectionRequests(self):
        self.socket.listen(1)
        if self.socket:
            try:
                newClient = ClientConnection(self, self.socket.accept())
                self.clients.append(newClient)
                self.serverInstance.cbl["onNewClient"].call({"clientConnection": newClient})
            except socket.error:
                self.listening = False
                return

    def serverCmd(self, cmd):
        cmd = cmd.strip()
        if cmd == 'disco':
            self.log("disconnect all clients")
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
            self.log("no client available")

    def disconnectClients(self):
        for client in self.clients:
            client.disconnect(True)
        self.clients = []

    def shutdown(self):
        #self.log("shutdown")
        self.listening = 0
        #self.log("disconnect clients")
        self.disconnectClients()
        #self.log("close socket")
        self.socketClose()
        self.log("shutdown done")

    def socketClose(self):
        if self.socket:
            try:
                self.socket.shutdown(socket.SHUT_RDWR)
                self.socket.close()
                self.socket = None
            except socket.error:
                print "socketClose failed"
                return

    def log(self, msg):
        self.logger.log("["+self.name+"][" + self.serverInstance.name + "] " + msg)

    def setLogger(self, logger):
        if logger:
            self.logger = logger
            self.log("logging enabled")

class ClientConnection(network.networkConnection):

    def __init__(self, server, client):
        network.networkConnection.__init__(self)
        self.server = server
        self.clientContainer = None
        self.cbl["onDataIncoming"].add(cb.CallbackCall(self.clientReceiving))
        self.clientInfo = client[1]
        self.clientStuff = client
        self.socket = client[0]
        self.start()
        self.logger = logger.logger()

    def __del__(self):
        self.disconnect(True)

    def disconnect(self, withDisco):
        self.log("disconnecting...")
        network.networkConnection.disconnect(self, withDisco)
        self.clientInfo = None
        if self.clientContainer:
            self.clientContainer.connection = None
            self.clientContainer = None
        if self in self.server.clients:
            self.server.clients.remove(self)
        self.log(".. done")

    def getClientString(self):
        if self.clientInfo:
            return "[" + self.clientInfo[0] + "]"
        return "[<unknown>]"

    def clientReceiving(self, attributes):
        #connection.log(" received: " + data)
        # DeviceServer clients does not have clientContainer
        if self.clientContainer:
            self.clientContainer.actionlogData=attributes["data"]
            self.clientContainer.actionlogNew.set()

    def log(self, msg):
        self.logger.log(self.getClientString() + " " + msg)

    def setLogger(self, logger):
        if logger:
            self.logger = logger
            self.log("logging enabled")

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

class Server:

    def __init__(self, name, ip, port):
        self.name = name
        self.ip = ip
        self.port = port
        self.cbl = cb.CallbackList({"onNewClient": cb.Callback()})
        self.srvlis = ServerListener(self)
        
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
        self.cbMapRefresh = None
        self.template = xmltemplate.Template()
        self.start()

    def assimilateActions(self, actionlog):
        """ turn the cliens action log into a map and if send, get some other infos """
        for action in actionlog.actions:
            # contains action and value
            dev, key = action.action.lower().split(":")


            if dev == "engine" and self.devs.has_key(dev):
                if key == "turned":
                    self.position.orientation += action.value
                    for dev in self.devs.values():
                        if dev.has_key("touch"):
                            dev["touch"] = False
                elif key == "distance":
                    newPos = self.position.getPointInDistance(action.value)

                    if ( self.devs.has_key("head")
                         and self.devs["head"].has_key("dimension")
                         and self.devs["head"].has_key("position")
                         and self.devs["head"]["position"] ):
                        for dev in self.devs:
                            if ( self.devs[dev].has_key("touch")
                                 and self.devs[dev]["touch"]
                                 and self.devs[dev].has_key("dimension")
                                 and self.devs[dev]["dimension"] ):
                                v_start = self.devs[dev]["dimension"].copy(map.Point(self.position.point.x, self.position.point.y),
                                                                           self.position.orientation)
                                v_end = self.devs[dev]["dimension"].copy(newPos, self.position.orientation)
                                # sensor at start position
                                self.map.borders.add(v_start)
                                # sensor on end position
                                self.map.borders.add(v_end)
                                # point 1 start to end
                                self.map.borders.add(map.Vector().combine(v_start, v_end, map.Vector.START_POINT))
                                # point 2 start to end
                                self.map.borders.add(map.Vector().combine(v_start, v_end, map.Vector.END_POINT))
                                # area marked as cleaned
                                self.map.addArea(v_start.getStartPoint(), v_start.getEndPoint(), v_end.getStartPoint())
                    self.position.point = newPos
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

        if self.cbMapRefresh:
            self.cbMapRefresh()

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
            self.connection.log("try to discover, but no \"radius\" item found" )

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
        if self.devs.has_key("self"):
            router = map.Router(self.devs["self"]["radius"])
            for wp in self.map.waypoints:
                if wp.duty & map.WayPoint.WP_FAST:
                router.actionRoute(pos, wp, self.getSensorList, self.template.addTemplate, self.map.getCollisions)
    
                if wp.duty & map.WayPoint.WP_STRICT:
                    collisions = self.map.getCollisions(pos, self.getSensorList(True), 0)
                    for i in range(len(collisions)):
                        if pos.point.getDistanceTo(wp) < collisions[i][0]:
                            break
                    router.actionRoute(pos, collisions[i][2], self.getSensorList, self.template.addTemplate, self.map.getCollisions)
                        if i < len(collisions)-1:
                            bpos = map.Position(collisions[i+1][2], pos.orientation+180)
                            bc = self.map.getCollisions(bpos, self.getSensorList(True), 0)
                            if len(bc) and pos.point.getDistanceTo(wp) < bc[0][0]:
                            router.actionRoute(pos, bc[0][2], self.getSensorList, self.template.addTemplate, self.map.getCollisions)
    
                if wp.duty & map.WayPoint.WP_DISCOVER:
                router.actionDiscover(pos, wp.attachment, cb_getSensorList=self.getSensorList, cb_addAction=self.template.addTemplate)
    
        xml = self.template.getTransmissionData()
        print "send: " + xml
        self.connection.write(xml)
            self.map.clearWaypoints()
        self.template.clear()

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
        Server.__init__(self, "MarvinServer",'127.0.0.1',29875)
        self.cbl["onNewClient"].add(cb.CallbackCall(self.addClient))
        self.clients = []

    def __del__(self):
        self.shutdown()

    def addClient(self, attributes):
        clientConnection = attributes["clientConnection"]
        clientConnection.clientContainer=ClientContainer()
        clientConnection.clientContainer.connection = clientConnection
        self.clients.append(clientConnection.clientContainer)
        if self.srvlis:
            self.srvlis.log("client added")

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
        Server.__init__(self, "DeviceServer",'127.0.0.1',29874)
        self.cbl["onNewClient"].add(cb.CallbackCall(self.addClient))

    def addClient(self, attributes):
        clientConnection = attributes["clientConnection"]
        clientConnection.cbl["onDataIncoming"].add(cb.CallbackCall(self.clientReceiving))

    def clientReceiving(self, attributes):
        self.broadcast(attributes["data"], [attributes["networkConnection"]])
    

if __name__ == '__main__':
    Shell()
    shellInstance.run()
