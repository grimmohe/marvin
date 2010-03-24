#!/usr/bin/env python
#coding=utf8

import os
import sys
import socket

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
        self.run()

    def run(self):
        self.listening = 1
        while self.listening:
            self.listen()
            self.processing = 1
            while self.processing:
                #self.procCmd()
                self.awaitingUserCommands()
            print "disco"
            self.client.close()
        print "server close"
        self.server.shutdown(socket.SHUT_RDWR)
        self.server.close()

    def listen(self):
        self.server.listen(5)
        print '...listening'
        cli = self.server.accept()
        self.client  = cli[0]
        print '...connected: ', cli[1]

    def procCmd(self):
        cmd = self.client.recv(BUFSIZE)
        if not cmd: return
        print cmd
        self.serverCmd(cmd)
        if self.processing:
            if cmd == "Gimme":
                self.client.send("DaHaste")

    def serverCmd(self, cmd):
        cmd = cmd.strip()
        if cmd == 'disco':
            self.processing = 0
        elif cmd == "kill":
            self.listening = self.processing = 0
            
    def awaitingUserCommands(self):
        cmd=''
        while self.processing:
            cmd = raw_input("cmd#>:")
            print cmd
            self.serverCmd(cmd)
            if self.processing:
                self.processUserCommand(cmd)

    def processUserCommand(self, cmd):
        cmd = cmd.replace("  "," ").strip().split(" ")
        if "sf" == cmd[0]:
            print "sending file:", cmd[1]
            if self.sendFile(cmd[1]) == 0:
                print "send ok"
            else:
                print "send failed"
                
        else:
            print "command unkown: ",cmd[0]
            print "sf <file>"
            print "disco"
            print "kill"
        
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

if __name__ == '__main__':
    serv = ServCmd()
