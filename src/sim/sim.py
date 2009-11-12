#!/usr/bin/env python
#coding=utf8

import os, time, string

class device:
    file = None
    cb_readevent = None

    def __init__(self, filename, cb_event):
        self.file = os.open(filename, os.O_RDWR | os.O_SYNC)
        self.cb_readevent = cb_event

    def read(self):
        data = os.read(self.file, 80)
        if len(data) > 0:
            self.cb_readevent(data)

    def write(self, data):
        os.write(self.file, data)
        os.lseek(self.file, 0, os.SEEK_END)

class cleaner:
    pos_x         = 20
    pos_y         = 20
    orientation   = 0
    radius        = 20
    speed         = 10 # 1/s

class room:
    height        = 400
    width         = 400

class simulator:
    sensor_right  = None
    sensor_left   = None
    sensor_front  = None
    engine        = None
    client        = cleaner()    # Unser Staubsaugerrepresentant
    room          = room()       # Die Spielwiese

    starttime     = None
    stoptime      = None         # Wann ist ads Hindernis erreicht?
    runit         = False

    def __init__(self):
        self.sensor_right  = device('/tmp/dev_right', self.cb_sensor_right)
        self.sensor_left   = device('/tmp/dev_left', self.cb_sensor_left)
        self.sensor_front  = device('/tmp/dev_front', self.cb_sensor_front)
        self.engine        = device('/tmp/dev_engine', self.cb_engine)

    def cb_sensor_right(self, data):
        pass

    def cb_sensor_left(self, data):
        pass

    def cb_sensor_front(self, data):
        pass

    def cb_engine(self, data):
        print data
        data = string.split(data, "=")
        if data[0] == "drive":
            if data[1] == "1": # berechne, wann das nächste Hinderniss erreicht ist
                self.starttime = time.clock()
            else:
                pass # welche Position haben wir bis jetzt erreicht?
        elif data[0] == "turn":
            self.client.orientation += string.atoi(data[1])
        elif data[0] == "shutdown\n":
            self.runit = False

    # Prüfen, ob Sensordaten zu senden sind
    def check(self):
        pass

    # Main loop
    def run(self):
        self.runit = True
        while self.runit:
            self.engine.read()
            self.check()
            time.sleep(0.01)

# Und lauf!
mysim = simulator()
mysim.run()

print "It's done!"



