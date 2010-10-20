#!/usr/bin/env python
#coding=utf8

import threading
import socket
import callback as cb

BUFSIZE = 4096

class networkConnection(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)
        self.cbl = cb.CallbackList({"onDataIncoming": cb.Callback(), 
                                    "onExternDisconnection": cb.Callback()})
        self.reader = None
        self.socket = None
        self.data = ''

    def __del__(self):
        #print "__del__ netCon <" + self.name + ">"
        self.disconnect(True)

    def run(self):
        #print "run netCon <" + self.name + ">"
        self.reader = networkConnectionReader(self)

    def disconnect(self, withDisco):
        #print "disco netCon <" + self.name + ">"
        if withDisco:
            self.write("DISCO")
        if self.reader:
            self.reader.stop = True
        self.reader = None
        if self.socket:
            try:
                self.socket.shutdown(socket.SHUT_RDWR)
                self.socket.close()
            except socket.error:
                print "socket not clean closed, but who cares, its the end"
        self.socket = None

    def write(self,data):
        if self.socket:
            try:
                self.socket.send(data + "\n\n")
                return True
            except socket.error:
                print "error while sending. effect? no idea, disconnect socket"
                self.disconnect(False)
                self.cbl["onExternDisconnection"].call({"networkConnection": self})
        return False

    def receive(self, data):
        if data == "DISCO":
            self.disconnect(False)
            self.cbl.call("onExternDisconnection", {"networkConnection": self})
            return
        self.data = data
        self.cbl["onDataIncoming"].call({"networkConnection": self, "data": data})

    def read(self,flushData=False):
        data = self.data
        if flushData:
            self.data = ''
        return data

    def getCallback(self, name):
        return self.cbl[name]

class networkConnectionReader(threading.Thread):

    def __init__(self,netCon):
        threading.Thread.__init__(self)
        self.netConnection = netCon
        self.stop = False
        self.start()

    def __del__(self):
        self.clientCon = None

    def run(self):
        self.awaitIncoming()

    def awaitIncoming(self):
        data = "" # in case of an exception, data would be unreferenced
        while not self.stop and self.netConnection.socket:
            try:
                data += self.netConnection.socket.recv(BUFSIZE)
            except socket.error:
                print "Unfriendly connection reset"
                return
            if not data:
                break
            if "\n\n" == data[-2:]:
                if self.netConnection:
                    self.netConnection.receive(data.strip("\n"))
                data=""