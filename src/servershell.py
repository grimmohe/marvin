#!/usr/bin/env python
#coding=utf8

import server
import logger
import ServerControl
import time

shellInstance = None

class Shell:

    def __init__(self):
        global shellInstance
        shellInstance = self
        self.marvinsc = None
        self.devsc = None
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
        elif "echo" == cmd[0]:
            print ' '.join(cmd)
        elif "exit" == cmd[0]:
            self.exit = True
        elif "start" == cmd[0]:
            self.runServers()
        elif "stop" == cmd[0]:
            self.destroyServers()
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
        if self.marvinsc and self.marvinsc.isRunning():
            self.marvinsc.destroy()
        self.marvinsc = None
        if self.devsc and self.devsc.isRunning():
            self.devsc.destroy()
        self.devsc = None

    def runServers(self):
        if not self.marvinsc:
            self.marvinsc = ServerControl.ServerControl("MarvinServer", ServerControl.SERVERTYPE_MARVINSRV)
            self.marvinsc.start()
        if not self.devsc:
            self.devsc = ServerControl.ServerControl("DeviceServer", ServerControl.SERVERTYPE_DEVICESRV)
            self.devsc.start()


if __name__ == '__main__':
    Shell()
    shellInstance.run()
