#!/usr/bin/env python
#coding=utf8

import os
import socket
import threading

BUFSIZE = 4096

class serverListener(threading.Thread):

    def __init__(self, name, shell, ip, port, cb_read):
        threading.Thread.__init__(self)
        self.socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.socket.bind((ip,port))
        self.listening  = 0
        self.clients = []
        self.shell = shell
        self.cb_read = cb_read
        self.name = name
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
            self.clients.append(clientConnection(self,cli,self.cb_read))

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
        self.cb_read(data)

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
        if "sf" == cmd[0]:
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

class DustServer(Server):

    def __init__(self,shell):
        Server.__init__(self,"DustSrv",shell,'',29875, self.CliendReceiving)

    def CliendReceiving(self, data):
        pass

class DeviceServer(Server):

    def __init__(self,shell):
        Server.__init__(self,"DevSrv",shell,'',29874, self.CliendReceiving)

    def CliendReceiving(self, data):
        self.broadcast(data)


if __name__ == '__main__':
    shell = shell()
    print "system exit"