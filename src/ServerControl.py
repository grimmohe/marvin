#!/usr/bin/env python
#coding=utf8

import threading
import server
import logger
import time
import callback as cb

SERVERTYPE_MARVINSRV=1
SERVERTYPE_DEVICESRV=2

class ServerControl(threading.Thread):

    def __init__(self, name, servertype):
        threading.Thread.__init__(self)
        self.event_SwitchState = threading.Event()
        self.servertype = servertype
        self.servername = name
        self.logger=logger.logger()
        self.stop = False
        self.server = None
        self.cbl= cb.CallbackList(["onRunning"])

    def run(self):
        self.log("running..")
        self.ServerStart()
        while not self.stop:
            self.event_SwitchState.clear()
            self.event_SwitchState.wait()
            self.log("event!")
            if self.stop:
                self.log("stopping...")
                if self.server:
                    self.ServerStop()
                self.log("leaving event loop")
                return
            if self.server:
                self.ServerStop()
            else:
                self.ServerStart()


    def ServerStop(self):
        self.log("stop server")
        if self.server:
            self.server.shutdown()
        self.server=None

    def ServerStart(self):
        self.log("start server")
        if not self.server:
            if self.servertype == SERVERTYPE_MARVINSRV:
                self.server = server.MarvinServer()
            if self.servertype == SERVERTYPE_DEVICESRV:
                self.server = server.DeviceServer()
            self.server.setLogger(self.logger)
            if self.ServerRun(50):
                self.log("done")
            else:
                self.log("failed")


    def ServerRun(self, maxTries):
        curTry = 0
        while curTry <= maxTries:
            self.log( "try to run " + str(curTry) + "/" + str(maxTries) )
            if self.server.run():
                self.cbl.call("onRunning", {"serverControl": self})
                return True
            curTry += 1
            time.sleep(5.0)
        return False

    def setStop(self, stop):
        self.stop = stop

    def isRunning(self):
        if self.server:
            return True
        return False

    def destroy(self):
        self.setLogger(logger.logger())
        self.server.setLogger(self.logger)
        self.log("destroy")
        if self.server:
            self.server.srvlis.setLogger(None)
        self.stop = True
        self.event_SwitchState.set()
        self.log("done..")
         
    def log(self, msg):
        self.logger.log("["+self.name+"]["+self.servername+"] ServerControl: "+msg)

    def setLogger(self, logger):
        if logger:
            self.logger = logger
            self.log("logging enabled")        
