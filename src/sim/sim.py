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
    last_write = None
    last_read = None

    def __init__(self, filename, cb_event):
        self.file = os.open(filename, os.O_RDWR | os.O_SYNC)
        self.cb_readevent = cb_event

    def read(self):
        data = os.read(self.file, 80)
        if len(data) > 0:
            self.cb_readevent(data)
            self.last_read = data

    def write(self, data):
        os.write(self.file, data)
        os.lseek(self.file, 0, os.SEEK_END)
        self.last_write = data

"""
Representant für den Staubsauger
"""
class cleaner:
    RADIUS        = 20.0
    SPEED         = 10.0 # 1/s
    SENSOR_RANGE  = 1.0
    head_form     = ( {"x": -10.0, "y":  0.0, "sensor": None, "id": "left",
                       "dev": "/tmp/dev_left",  "status": 1.0}
                    , {"x": -10.0, "y": 10.0, "sensor": None, "id": "front",
                       "dev": "/tmp/dev_front", "status": 1.0}
                    , {"x":  10.0, "y": 10.0, "sensor": None, "id": "right",
                       "dev": "/tmp/dev_right", "status": 1.0}
                    , {"x":  10.0, "y":  0.0, "sensor": None, "id": "",
                       "dev": "",               "status": 1.0} )
    head_down     = False
    index         = 0

    startposition = {"x": 20.0, "y": 20.0}
    starttime     = None
    orientation   = 0.0

    def __init__(self):
        def cb_sensor_dummy(): # auf diesen Devices wird nur gesendet
            pass
        for point in self.head_form:
            if len(point["dev"]) > 0:
                point["sensor"] = device(point["dev"], cb_sensor_dummy)

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

    def get_head_site(self, first=False):
        if first:
            self.index = 0
        if self.index + 1 >= len(self.waypoints):
            return None
        index += 1
        line = (self.waypoints[(index - 1) % len(self.waypoints)],
                self.waypoints[(index) % len(self.waypoints)])
        line[1]["sensor"] = line[0]["sensor"]
        line[1]["id"]     = line[0]["id"]
        line[1]["dev"]    = line[0]["dev"]
        return line

    def reset_head_status(self):
        for sensor in self.head_form:
            sensor["status"] = 1.0

"""
Datenhalter für Rauminformationen
"""
class room:
    waypoints = []
    index     = 0

    """
    Lädt eine Datei wp_file im Format x;y \n x;y
    Die Strecken von einem Punkt zum nächsten bilden die Wände des Raumen, in
    dem wir uns befinden.
    """
    def __init__(self, wp_file):
        self.waypoints = []
        file = open(wp_file, "r")
        for line in file.readlines():
            split = string.split(line, ";")
            self.waypoints.append({ "x": string.atoi(split[0])
                                  , "y": string.atoi(split[1]) })
            print self.waypoints
        file.close()

    """
    Liefert eine Strecke ({"x": int, "y": int}, {"x": int, "y": int}).
    Jeder weitere Aufruf leifert die nächste Strecke. Wurden alle Strecken
    ausgegeben, wird None zurückgegeben.
    Mit first = True wird der interne Zähler zurückgesetzt.
    """
    def get_line(self, first=False):
        if first:
            self.index = 0
        if self.index >= len(self.waypoints):
            return None
        index += 1
        return (self.waypoints[(index - 1) % len(self.waypoints)],
                self.waypoints[(index) % len(self.waypoints)])


"""
Physiksimulator für den Client
"""
class simulator:
    engine        = None
    runit         = False
    client        = None
    room          = None

    def __init__(self):
        self.engine        = device('/tmp/dev_engine', self.cb_engine)
        self.client        = cleaner()
        self.room          = room("../data/room.xy")

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
    def check(self, now):
        client_pos = self.client.get_cur_position(now)
        self.client.reset_head_status()
        line       = self.room.get_line(True)
        while line:
            # Steigungsfaktor von line
            a_line  = ( (line[0]["y"] - line[1]["y"])
                      / (line[0]["x"] - line[1]["x"]) )
            a0_line = line[0]["y"] - a_line * line[0]["x"]

            sensor = self.client.get_head_site(True)
            while sensor:
                # Steigungsfaktor von sensor
                a_sensor  = ( (sensor[0]["y"] - sensor[1]["y"])
                            / (sensor[0]["x"] - sensor[1]["x"]) )
                a0_sensor = sensor[0]["y"] - a_sensor * sensor[0]["x"]
                # Schnittpunkt
                # y = f(x) = a * x
                y_s = ( (a_line * line[0]["x"] + a0_line)
                      - (a_sensor * sensor[0]["x"] + a0_sensor) )

                sensor = self.client.get_head_site()
            line = self.room.get_line()

    # Main loop
    def run(self):
        self.runit = True
        while self.runit:
            timestamp = time.time()
            # Komunikationsdateien checken
            self.engine.read()
            # Kollisionskontrolle
            self.check(timestamp)
            # warten, aber bitte alle 0.01 aufwachen
            time.sleep(max(0, 0.01 - (time.time() - timestamp)))

# Und lauf!
mysim = simulator()
mysim.run()

print "It's done!"



