#!/usr/bin/env python
#coding=utf8

import os
import socket
import threading
import network
import map
import common
import gc
from pprint import pprint

shellInstance = None

class serverListener(threading.Thread):

    def __init__(self, server, cb_read):
        threading.Thread.__init__(self)
        self.listening  = 0
        self.clients = []
        self.cb_read = cb_read
        self.cb_newClient = None
        self.serverInstance=server

    def __del__(self):
        self.shellEcho("destroy serverListener")
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
        #self.shellEcho("server is listening")
        self.socket.listen(1)
        if self.socket:
            try:
                newClient = self.socket.accept()
                newClient = clientConnection(self,newClient,self.cb_read)
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
                    self.clients[0].write(stream)
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
        print("echo [" + self.serverInstance.name + "] " + msg)


class clientConnection(network.networkConnection):

    def __init__(self, server, client, cb_read):
        network.networkConnection.__init__(self)
        self.server = server
        self.clientContainer = None
        self.clientInfo = client[1]
        self.clientStuff = client
        self.cbDataIncome = cb_read
        self.socket = client[0]
        self.start()

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
        self.server.shellEcho(self.getClientString() + " " + msg)

class shell:

    def __init__(self):
        global shellInstance
        shellInstance = self
        self.marvinsrv = None
        self.devsrv = None
        self.exit = False

    def __del__(self):
        print "destroy shell"
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
        self.processCommand("echo close shell")

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
        while curTry <= maxTries:
            print "try to run " + srv.name + " (" + str(curTry) + "/" + str(maxTries) + ")"
            if srv.run():
                return True
            tries += 1
            time.sleep(1.0)
        return False

class Server:

    def __init__(self, name, ip, port, cb_read):
        self.name = name
        self.ip = ip
        self.port = port
        self.srvlis = serverListener(self, cb_read)

    def __del__(self):
        self.srvlis = None

    def broadcast(self,data,exceptConnections):
        for client in self.srvlis.clients:
            if not client in exceptConnections:
                client.write(data)

    def run(self):
        if self.srvlis:
            return self.srvlis.bind(self.ip, self.port)
        return False

class ClientContainer(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)
        self.orientation = 0.0
        self.map = map.Map()
        self.vSensorLeft = map.Vector(-20.0, 0.0, 0.0, -20.0)
        self.vSensorFront = map.Vector(-20.0, 20.0, -40.0, -0.0)
        self.vSensorRight = map.Vector(20.0, 0.0, 0.0, -20.0)
        self.connection = None
        self.actionlog = common.Actionlog()
        self.actionlogData = ""
        self.actionlogNew = threading.Event()
        self.stop = False
        self.start()

    def run(self):
        while not self.stop:
            self.actionlogNew.clear()
            self.actionlogNew.wait()
            if self.actionlogData and self.actionlog:
                self.actionlog.readXml(self.actionlogData)
            #self.connection.shellEcho("actionlog parsed")

    def shutdown(self):
        if self.connection:
            self.connection.clientContainer = None
        self.connection = None
        self.actionlog = None
        # semi fire event to come out of wait state, but set stop flag before, so thread
        # is killed
        self.stop = True
        self.actionlogNew.set()
        self.actionlogNew = None
        self.map = None

class MarvinServer(Server):

    def __init__(self):
        Server.__init__(self, "MarvinServer",'127.0.0.1',29875, self.ClientReceiving)
        self.srvlis.cb_newClient=self.addClient
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
            client_con.shellEcho("no suitable client found")

    def Actionlog2Vector(self, cc):
        """ cc = ClientConnector() """

    def addClient(self, con):
        con.clientContainer=ClientContainer()
        con.clientContainer.connection = con
        self.clients.append(con.clientContainer)
        self.srvlis.shellEcho("client added")

    def shutdown(self):
        for client in self.clients:
            client.shutdown()
            del client
            client=None
        self.clients=[]
        if self.srvlis:
            self.srvlis.shutdown()
            self.srvlis = None

class DeviceServer(Server):

    def __init__(self):
        Server.__init__(self, "DeviceServer",'127.0.0.1',29874, self.ClientReceiving)

    def ClientReceiving(self, connection, data):
        self.broadcast(data, [connection])


if __name__ == '__main__':
    shell()
    shellInstance.run()
