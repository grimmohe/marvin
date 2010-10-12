#!/usr/bin/env python
#coding=utf8

import device
import server
import time

lastsending = ''
count = 0
maxcount = 100

def cbA(data):
    print "A " + data

def cbB(data):
    print "B " + data

print "start dev srv"
devsrv = server.DeviceServer()
devsrv.run()

time.sleep(5)

print "init devs"
dev1 = device.Device("A", cbA)
dev2 = device.Device("A", cbB)

time.sleep(5)

while count <= maxcount:
    lastsending = "teststring=" + str(count)
    print lastsending
    if not dev1.write(lastsending):
        print "send failed"
    count += 1

time.sleep(5)

dev1.close()
dev2.close()
dev1=None
dev2=None
devsrv.shutdown()
devsrv = None

