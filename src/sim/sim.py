#!/usr/bin/env python
#coding=utf8

import os, time, string, math

"""
Beobachtet eine Datei, indem regelmäßig read() aufgerufen wird.
Schreibt in selbige Datei mit write(data).
Sollten mit read() neue Informationen gelesen werden, wird
cb_readevent ausgelöst.
"""
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

"""
Representant für den Staubsauger
"""
class cleaner:
    RADIUS        = 20.0
    SPEED         = 10.0 # 1/s

    startposition = {"x": 20.0, "y": 20.0}
    starttime     = None
    orientation   = 0.0

    """
    Setzt die eigene Position aus der Ursprungsposition, Ausrichtung und
    Bewegung als neue Ausgangslage.
    """
    def set_position(self, current_time):
        self.startposition = self.get_cur_position(current_time)
        self.starttime     = current_time
        return 1

    """
    Berechnet die aktuelle Position aus Ursprungsposition, Ausrichtung und
    Bewegung.
    returns {"x": int, "y": int}
    """
    def get_cur_position(self, current_time):
        if self.starttime == None:
            return self.startposition

        new_pos = {"x": None, "y": None}
        distance = self.SPEED * (current_time - self.starttime)

        # c = distance
        # Alpha = orientation MOD 90°
        # also Sin Alpha = a/c -> a = Sin Alpha * c
        # und  Cos Altha = b/c -> b = Cos Alpha * c
        alpha = math.radians(self.orientation % 90)
        a = math.sin(alpha) * distance
        b = math.cos(alpha) * distance

        part = round(self.orientation / 90)
        if part == 0:
            new_pos["x"] = self.startposition["x"] + a
            new_pos["y"] = self.startposition["y"] + b
        elif part == 1:
            new_pos["x"] = self.startposition["x"] + b
            new_pos["y"] = self.startposition["y"] - a
        elif part == 2:
            new_pos["x"] = self.startposition["x"] - a
            new_pos["y"] = self.startposition["y"] - b
        elif part == 3:
            new_pos["x"] = self.startposition["x"] - b
            new_pos["y"] = self.startposition["y"] + a

        return new_pos

"""
Datenhalter für Rauminformationen
"""
class room:
    height        = 400
    width         = 400

"""
Physiksimulator für den Client
"""
class simulator:
    sensor_right  = None
    sensor_left   = None
    sensor_front  = None
    engine        = None
    runit         = False

    client        = cleaner()    # Unser Staubsaugerrepresentant
    room          = room()       # Die Spielwiese

    def __init__(self):
        self.sensor_right  = device('/tmp/dev_right',  self.cb_sensor_right)
        self.sensor_left   = device('/tmp/dev_left',   self.cb_sensor_left)
        self.sensor_front  = device('/tmp/dev_front',  self.cb_sensor_front)
        self.engine        = device('/tmp/dev_engine', self.cb_engine)

    def cb_sensor_right(self, data):
        pass

    def cb_sensor_left(self, data):
        pass

    def cb_sensor_front(self, data):
        pass

    """
    Der einzige CallBack, von dem Daten erwartet werden
    """
    def cb_engine(self, data):
        print data
        data = string.split(data, "=")
        if data[0] == "drive":
            if data[1] == "1":
                self.starttime = time.time()
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
            timestamp = time.time()
            # Komunikationsdateien checken
            self.engine.read()
            self.sensor_front.read()
            self.sensor_left.read()
            self.sensor_right.read()
            # Kollisionskontrolle
            self.check()
            # warten, aber bitte alle 0.01 aufwachen
            time.sleep(max(0, 0.01 - (time.time() - timestamp)))

# Und lauf!
mysim = simulator()
mysim.run()

print "It's done!"



