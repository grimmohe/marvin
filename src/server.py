#!/usr/bin/env python
#coding=utf8

import os
import socket
import threading
import network
import map
import common

shellInstance = None

class serverListener(threading.Thread):

    def __init__(self, server, ip, port, cb_read):
        threading.Thread.__init__(self)
        self.socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        try:
            self.socket.bind((ip,port))
        except socket.error:
            print "socket error"
            #TODO: Korrektes exception handling
        self.listening  = 0
        self.clients = []
        self.cb_read = cb_read
        self.cb_newClient = None
        self.serverInstance=server
        self.start()

    def __del__(self):
        self.shellEcho("destroy server")
        self.socket = None

    def run(self):
        self.listening = 1
        while self.listening and self.socket:
            self.listenForConnectionRequests()
        self.shellEcho("server shutdown")
        self.shutdown()

    def listenForConnectionRequests(self):
        self.shellEcho("server is listening")
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
            client.disconnect()
        self.clients = []

    def shutdown(self):
        self.shellEcho("try killing me")
        self.listening = 0
        self.disconnectClients()
        self.socketClose()
        self.shellEcho("done???")

    def socketClose(self):
        if self.socket:
            try:
                self.socket.shutdown(socket.SHUT_RDWR)
                self.socket.close()
            except socket.error:
                print "socketClose failed"
                return

    def shellEcho(self, msg):
        global shellInstance
        shellInstance.processCommand("echo [" + self.serverInstance.name + "] " + msg)


class clientConnection(network.networkConnection):

    def __init__(self, server, client, cbRead):
        network.networkConnection.__init__(self)
        self.server = server
        self.clientContainer = None
        self.clientInfo = client[1]
        self.clientStuff = client
        self.cbRead = cbRead
        self.socket = client[0]
        self.start()

    def __del__(self):
        self.disconnect()

    def disconnect(self):
        self.server.shellEcho("disconnecting...")
        network.networkConnection.disconnect(self)
        self.clientInfo = None
        self.shellEcho(".. done")

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
        self.marvinsrv = MarvinServer()
        self.devsrv = DeviceServer()
        self.exit = False
        self.run()

    def __del__(self):
        print "destroy shell"
        self.destroyServers()


    def run(self):
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
            if not self.marvinsrv:
                self.marvinsrv = DustServer(self)
            if not self.devsrv:
                self.devsrv = DeviceServer(self)
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
            self.marvinsrv.srvlis.shutdown()
            self.marvin = None
        if self.devsrv:
            self.devsrv.srvlis.shutdown()
            self.devsrv = None

class Server:

    def __init__(self, name, ip, port, cb_read):
        self.name = name
        self.srvlis = serverListener(self, ip, port, cb_read)

    def __del__(self):
        self.srvlis = None

    def broadcast(self,data,exceptClients):
        for client in self.srvlis.clients:
            if not client in exceptClients:
                client.send(data)

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
        self.start()

    def run(self):
        while True:
            self.actionlogNew.clear()
            self.actionlogNew.wait()
            self.actionlog.readXml(self.actionlogData)
            self.connection.shellEcho("actionlog parsed")

    def shutdown(self):
        pass

class MarvinServer(Server):

    def __init__(self):
        Server.__init__(self, "MarvinServer",'127.0.0.1',29875, self.ClientReceiving)
        self.srvlis.cb_newClient=self.addClient
        self.clients = []

    def ClientReceiving(self, client_con, data):
        client_con.shellEcho(" received: " + data)
        client = None
        for c in self.clients:
            if c.connection == client_con:
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
            client=None
        self.clients=None

class DeviceServer(Server):

    def __init__(self):
        Server.__init__(self, "DeviceServer",'127.0.0.1',29874, self.ClientReceiving)

    def ClientReceiving(self, client, data):
        self.broadcast(data, [client])


if __name__ == '__main__':
    shell()
    print "system exit"