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

class ServCmd:
    def __init__(self):
        self.server = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.server.bind((ADDR))
        self.client = None
        self.listening  = 0
        self.processing = 0
        self.shell = shell(self)
        self.run()

    def run(self):
        self.listening = 1
        while self.listening:
            self.listen()
            self.processing = 1
            while self.processing:
                data = self.server.recv(BUFSIZE)
                print data
            self.shell.processCommand("echo disco")
            self.client.close()
        self.shell.processCommand("echo server closed")
        self.server.shutdown(socket.SHUT_RDWR)
        self.shell.close()
        self.server.close()

    def listen(self):
        self.server.listen(5)
        self.shell.processCommand("echo ...listening")
        cli = self.server.accept()
        self.client  = cli[0]
        self.shell.processCommand('echo ...connected: ' + cli[1][0] )

    def serverCmd(self, cmd):
        cmd = cmd.strip()
        if cmd == 'disco':
            self.shell.processCommand("echo disconnection")
            self.processing = 0
        elif cmd == "kill":
            self.shell.processCommand("echo try killing me")
            self.listening = self.processing = 0
            del self.server

    def sendFile(self, file):
        ofile = os.open(file, os.O_RDONLY)
        rc=1
        while True:
            stream = os.read(ofile, 2048)
            if len(stream) > 0:
                self.client.send(stream)
                rc = 0
            else:
                break
        os.close(ofile)
        return rc

class shell(threading.Thread):

    def __init__(self,server):
        threading.Thread.__init__(self)
        self.server = server
        self.start()

    def run(self):
        self.awaitingCommands()

    def awaitingCommands(self):
        cmd=''
        while True:
            cmd = raw_input("cmd#>:")
            self.processCommand(cmd)

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
        elif "srv" == cmd[0]:
            self.server.serverCmd(cmd[1])
        elif "help" == cmd[0]:
            print "command unkown: ",cmd[0]
            print "sf <file>"
            print "echo <text>"
            print "srv disco|kill"
            print "help"

    def closeCmdLine(self):
        self.processCommand("echo close shell")



if __name__ == '__main__':
    serv = ServCmd()
