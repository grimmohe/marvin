#!/usr/bin/env python
#coding=utf8

import os
import sys
import socket
import threading

BUFSIZE = 4096
HOST = ''
PORT = 29875
ADDR = (HOST,PORT)

class serverListener(threading.Thread):
    def __init__(self, shell):
        threading.Thread.__init__(self)
        self.server = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.server.bind((ADDR))
        self.listening  = 0
        self.clients = []
        self.shell = shell
        self.start()

    def __del__(self):
        self.shell.processCommand("echo server destroyed")
        
    def run(self):
        self.listening = 1
        while self.listening:
            self.listen()
        self.shell.processCommand("echo server shutdown")
        self.shutdown()

    def listen(self):
        self.shell.processCommand("echo server is listening")
        self.server.listen(5)
        if self.server:
            cli = self.server.accept()
            self.clients.append(clientConnection(self,cli))

    def serverCmd(self, cmd):
        cmd = cmd.strip()
        if cmd == 'disco':
            self.shell.processCommand("echo disconnect all clients")
            self.disconnectClients()
        elif cmd == "kill":
            self.shutdown()

    def sendFile(self, file):
        ofile = os.open(file, os.O_RDONLY)
        rc=1
        while True:
            stream = os.read(ofile, 2048)
            if len(stream) > 0:
                self.clients[0].send(stream)
                rc = 0
            else:
                break
        os.close(ofile)
        return rc

    def disconnectClients(self):
        for client in self.clients:
            client.disconnect()
        self.clients = []
    
    def shutdown(self):
        self.shell.processCommand("echo try killing me")
        self.listening = 0
        self.disconnectClients()
        self.server.shutdown(socket.SHUT_RDWR)
        self.server.close()
        self.shell.processCommand("echo done???")

class clientConnection(threading.Thread):
    
    def __init__(self, server, client):
        threading.Thread.__init__(self)
        self.server = server
        self.client = client[0]
        self.clientInfo = client[1]
        self.reader = None 
        self.start()

    def __del__(self):
        self.disconnect()

    def run(self):
        self.reader = clientConnectionReader(self)
        self.shellEcho("connected")

    def disconnect(self):
        self.shellEcho("disconnecting...")
        self.send("DISCO")
        self.reader.stop = True
        self.client.shutdown(socket.SHUT_RDWR)
        self.client.close()
        self.reader = None
        self.client = None
        self.clientInfo = None
        self.shellEcho(".. done")
        
    def send(self, data):
        self.shellEcho("something was send")
        self.client.send(data)
        
    def receive(self,data):
        self.shellEcho("something has been received: " + data)
        if data == "DISCO":
            self.reader.stop = True
        
    def getClientString(self):
        if self.clientInfo:
            return "[" + self.clientInfo[0] + "]"
        return "[<unknown>]"
    
    def shellEcho(self, msg):
        self.server.shell.processCommand("echo " + self.getClientString() + " " + msg)
        
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
        while not self.stop:
            data = self.clientCon.client.recv(BUFSIZE)
            self.clientCon.receive(data)
       

class shell():

    def __init__(self):
        self.server = serverListener(self)
        self.exit = False
        self.run()

    def run(self):
        self.awaitingCommands()

    def awaitingCommands(self):
        self.exit = False
        while not self.exit:
            cmd = raw_input("cmd#>: ")
            self.processCommand(cmd)
        if self.server:
            self.server = None

    def processCommand(self,cmd):
        if len(cmd) == 0:
            return

        cmd = cmd.replace("  "," ").strip().split(" ")
        if "sf" == cmd[0]:
            print "sending file: ", cmd[1]
            if self.server.sendFile(cmd[1]) == 0:
                print "send ok"
            else:
                print "send failed"
        elif "echo" == cmd[0]:
            print ' '.join(cmd)
        elif "exit" == cmd[0]:
            self.exit = True
        elif "start" == cmd[0]:
            if not self.server:
                self.server = serverListener(self)
        elif "stop" == cmd[0]:
            if self.server:
                self.server.shutdown()
                self.server = None
        elif "srv" == cmd[0]:
            if self.server:
                self.server.serverCmd(cmd[1])
        elif "help" == cmd[0]:
            print "command unkown: ",cmd[0]
            print "sf <file>"
            print "echo <text>"
            print "start|stop (a server instance)"
            print "srv disco|kill"
            print "help"

    def closeCmdLine(self):
        self.processCommand("echo close shell")



if __name__ == '__main__':
    shell = shell()
    print "system exit"