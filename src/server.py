#!/usr/bin/env python
#coding=utf8

import socket
import threading
import network
import logger
import ClientContainer as cc
import callback as cb

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
        except IOError, (errno, strerror):
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
        if self in self.server.clients:
            self.server.clients.remove(self)
        self.log(".. done")

    def getClientString(self):
        if self.clientInfo:
            return "[" + self.clientInfo[0] + "]"
        return "[<unknown>]"

    def log(self, msg):
        self.logger.log(self.getClientString() + " " + msg)

    def setLogger(self, logger):
        if logger:
            self.logger = logger
            self.log("logging enabled")


class Server:

    def __init__(self, name, ip, port):
        self.name = name
        self.ip = ip
        self.port = port
        self.cbl = cb.CallbackList(["onNewClient"])
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


class MarvinServer(Server):

    def __init__(self):
        Server.__init__(self, "MarvinServer",'127.0.0.1',29875)
        self.cbl["onNewClient"].add(cb.CallbackCall(self.addClient))
        self.cbl.add(["onNewClientContainer"])
        self.clients = []

    def __del__(self):
        self.shutdown()

    def addClient(self, attributes):
        clientContainer=cc.ClientContainer(attributes["clientConnection"])
        self.clients.append(clientContainer)
        self.cbl.call("onNewClientContainer", {"clientContainer": clientContainer})
        if self.srvlis:
            self.srvlis.log("client added")

    def removeClient(self, clientConnection):
        for cli in self.clients:
            if cli.clientConnection == clientConnection:
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
