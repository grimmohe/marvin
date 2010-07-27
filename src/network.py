#!/usr/bin/env python
#coding=utf8

import threading
import socket

BUFSIZE = 4096

class networkConnection(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)
        self.cbDataIncome = None
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
                print "error while sending, effect? no idear"
        return False

    def receive(self, data):
        self.data = data
        if data == "DISCO":
            self.disconnect(False)
            return
        if self.cbDataIncome:
            self.cbDataIncome(self, data)
        else:
            print "data recieved, bot no callback", data

    def read(self,flushData=False):
        data = self.data
        if flushData:
            self.data = ''
        return data

class networkConnectionReader(threading.Thread):

    def __init__(self,netCon):
        threading.Thread.__init__(self)
        self.netConnection = netCon
        self.stop = False
        self.start()

    def __del__(self):
        #print "__del__ netConReader <" + self.name + ">"
        self.clientCon = None

    def run(self):
        #print "run netConReader <" + self.name + ">"
        self.awaitIncoming()

    def awaitIncoming(self):
        data = "" # in case of an exception, data would be unreferenced
        while not self.stop and self.netConnection.socket:
            try:
                data += self.netConnection.socket.recv(BUFSIZE)
            except socket.error:
                print "Unfriendly connection reset"
            if not data:
                break
            if "\n\n" == data[-2:]:
                if self.netConnection:
                    self.netConnection.receive(data.strip("\n"))
                data=""