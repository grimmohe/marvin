#!/usr/bin/env python
#coding=utf8

import os
import sys
import socket

BUFSIZE = 4096
HOST = ''
PORT = 29876
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
                self.procCmd()
            self.client.close()
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
        if cmd == 'BYE':
            self.processing = 0
        elif cmd == "KILL":
            self.listening = self.processing = 0

if __name__ == '__main__':
    serv = ServCmd()
