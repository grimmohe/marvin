#!/usr/bin/env python
#coding=utf8

import server
import logger
import time

shellInstance = None

class Shell:

    def __init__(self):
        global shellInstance
        shellInstance = self
        self.marvinsrv = None
        self.devsrv = None
        self.exit = False
        self.tmplts = None
        self.logger = logger.logger()

    def __del__(self):
        print "destroy Shell"
        self.destroyServers()


    def run(self):
        self.processCommand("start")
        print "run Shell"
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
            self.runServers()
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
        self.processCommand("echo close Shell")

    def destroyServers(self):
        if self.marvinsrv:
            self.marvinsrv.shutdown()
        self.marvinsrv = None
        if self.devsrv:
            self.devsrv.srvlis.shutdown()
        self.devsrv = None

    def runServers(self):
        if not self.marvinsrv:
            self.marvinsrv = server.MarvinServer()
            self.runServer(self.marvinsrv, 50)
        if not self.devsrv:
            self.devsrv = server.DeviceServer()
            self.runServer(self.devsrv, 50)

    def runServer(self, srv, maxTries):
        curTry = 0
        srv.setLogger(self.logger)
        while curTry <= maxTries:
            print "try to run " + srv.name + " (" + str(curTry) + "/" + str(maxTries) + ")"
            if srv.run():
                return True
            curTry += 1
            time.sleep(5.0)
        return False



if __name__ == '__main__':
    Shell()
    shellInstance.run()
