#!/usr/bin/env python
#coding=utf8

import os
import socket
import threading
import common
import map
from map import Vector

BUFSIZE = 4096

class serverListener(threading.Thread):

    def __init__(self, name, shell, ip, port, cb_read):
        threading.Thread.__init__(self)
        self.socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        try:
            self.socket.bind((ip,port))
        except socket.error:
            print "socket error"
            #TODO: Korrektes exception handling
        self.listening  = 0
        self.clients = []
        self.shell = shell
        self.cb_read = cb_read
        self.name = name
        self.cb_newcli=None
        self.start()

    def __del__(self):
        self.shellEcho("destroy server")
        self.socket = None

    def run(self):
        self.listening = 1
        while self.listening and self.socket:
            self.listen()
        self.shellEcho("server shutdown")
        self.shutdown()

    def listen(self):
        self.shellEcho("server is listening")
        self.socket.listen(1)
        if self.socket:
            cli = self.socket.accept()
            cli = clientConnection(self,cli,self.cb_read)
            self.clients.append(cli)
            if self.cb_newcli:
                self.cb_newcli(cli)

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
                    self.clients[0].send(stream)
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
            self.socket.shutdown(socket.SHUT_RDWR)
            self.socket.close()

    def shellEcho(self, msg):
        self.shell.processCommand("echo [" + self.name + "] " + msg)


class clientConnection(threading.Thread):

    def __init__(self, server, client, cb_read):
        threading.Thread.__init__(self)
        self.server = server
        self.client = client[0]
        self.clientContainer = None
        self.clientInfo = client[1]
        self.clientStuff = client
        self.reader = None
        self.cb_read = cb_read
        self.start()

    def __del__(self):
        self.disconnect()

    def run(self):
        self.reader = clientConnectionReader(self)
        self.shellEcho("connected")

    def disconnect(self):
        self.shellEcho("disconnecting...")
        self.reader.stop = True
        if self.client:
            self.client.shutdown(socket.SHUT_RDWR)
            self.client.close()
        self.reader = None
        self.client = None
        self.clientInfo = None
        self.shellEcho(".. done")

    def send(self, data):
        try:
            self.client.send(data + "\n\n")
        except socket.error:
            self.shellEcho("Connection disbanded")

    def receive(self,data):
        if data == "DISCO" and self.reader:
            self.reader.stop = True
        self.cb_read(self, data)

    def getClientString(self):
        if self.clientInfo:
            return "[" + self.clientInfo[0] + "]"
        return "[<unknown>]"

    def shellEcho(self, msg):
        self.server.shellEcho(self.getClientString() + " " + msg)

class clientConnectionReader(threading.Thread):

    def __init__(self, clientCon):
        threading.Thread.__init__(self)
        self.clientCon = clientCon
        self.stop = False
        self.start()

    def __del__(self):
        self.clientCon = None

    def run(self):
        self.awaitIncoming()

    def awaitIncoming(self):
        data = "" # in case of an exception, data would be unreferenced
        while not self.stop:
            try:
                data = self.clientCon.client.recv(BUFSIZE).strip("\n")
            except socket.error:
                print "Unfriendly connection reset"
            if not data:
                self.clientCon.shellEcho("client disconnected")
                break
            self.clientCon.receive(data)
        self.clientCon.server.clients.remove(self.clientCon)
        self.clientCon = None


class shell:

    def __init__(self):
        self.dustsrv = DustServer(self)
        self.devsrv = DeviceServer(self)
        self.exit = False
        self.run()

    def __del__(self):
        print "destroy shell"
        self.destroyServers()


    def run(self):
        self.awaitingCommands()

    def awaitingCommands(self):
        self.exit = False
        while not self.exit:
            cmd = raw_input("cmd#>: ")
            self.processCommand(cmd)
        self.processCommand("stop")

    def processCommand(self,cmd):
        if len(cmd) == 0:
            return

        cmd = cmd.replace("  "," ").strip().split(" ")
        if "sft" == cmd[0]:
            self.processCommand("sf ../doc/test.xml")
        elif "sf" == cmd[0]:
            print "sending file: ", cmd[1]
            if self.dustsrv.srvlis.sendFile(cmd[1]) == 0:
                print "send ok"
            else:
                print "send failed"
        elif "echo" == cmd[0]:
            print ' '.join(cmd)
        elif "exit" == cmd[0]:
            self.exit = True
        elif "start" == cmd[0]:
            if not self.dustsrv:
                self.dustsrv = DustServer(self)
            if not self.devsrv:
                self.devsrv = DeviceServer(self)
        elif "stop" == cmd[0]:
            self.destroyServers()
        elif "srv" == cmd[0]:
            if self.dustsrv:
                self.dustsrv.srvlis.serverCmd(cmd[1])
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
        if self.dustsrv:
            self.dustsrv.srvlis.shutdown()
            self.dustsrv = None
        if self.devsrv:
            self.devsrv.srvlis.shutdown()
            self.devsrv = None

class Server:

    def __init__(self,name,shell,ip,port,cb_read):
        self.srvlis = serverListener(name, shell,ip,port,cb_read)

    def __del__(self):
        self.srvlis = None

    def broadcast(self,data):
        for client in self.srvlis.clients:
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

class DustServer(Server):

    def __init__(self,shell):
        Server.__init__(self,"DustSrv",shell,'',29875, self.ClientReceiving)
        self.srvlis.cb_newcli=self.addClient
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

    def __init__(self,shell):
        Server.__init__(self,"DevSrv",shell,'',29874, self.ClientReceiving)

    def ClientReceiving(self, client, data):
        self.broadcast(data)


if __name__ == '__main__':
    shell = shell()
    print "system exit"