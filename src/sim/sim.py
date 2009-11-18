#!/usr/bin/env python
#coding=utf8

import os, time, string, math

# Steigungsfaktor
def get_m(point1, point2={"x": 0, "y": 0}):
    return ( (point1[0]["y"] - point2[1]["y"])
             / (point1[0]["x"] - point2[1]["x"]) )

# Schnittpunkt mit Y
def get_n(point, m):
    return (point["y"] - m * point["x"])

# s = Schnittpunkt bis Punkt
def get_s(point, x=0, y=0):
    return math.sqrt( math.pow(x - point["x"], 2)
                      + math.pow(y - point["y"], 2) )

# h = die Höhe auf dem Sensor
def get_hs(ss, angle):
    return math.tan(math.radians(angle)) * ss

# h = die Höhe auf dem Sensor
def get_hl(sl, angle):
    return math.sin(math.radians(angle)) * sl

# lss = Schnittpunkt von h auf linie
def get_lss(b, angle):
    return b / math.cos(math.radians(angle))

# lsl = wie lss, nur von s von lien ausgehend
def get_lsl(c, angle):
    return math.cos(math.radians(angle)) * c

# Vergleicht, ob b zwischen a1/a2 liegt
def in_comp(a1, a2, b):
    return min(a1, a2) < b < max(a1, a2)

# Dreht einen Punkt auf der Systemachse
def turn_point(point, degrees):
    s = get_s(point)
    alpha = math.atan(get_m(point)) + math.radians(degrees)
    return { "x": s * math.sin(alpha),
             "y": s * math.cos(alpha) }

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
    """
    Liefert eine Liste von Strecken:
    (({"x": int, "y": int, "m": int, "n": int}, {"x": int, "y": int}), ...)
    """
    def get_head_lines(self):
        lines = ()
        if not self.head_down:
            return lines
        max   = len(self.head_form) - 1
        for i in range(len(self.head_form)):
            if self.head_form[i]["id"] <> "":
                sensor = ( simulator.turn_point(self.head_form[i % max],
                                                self.orientation),
                           simulator.turn_point(self.head_form[(i+1) % max],
                                                self.orientation) )
                sensor[0]["m"] = simulator.get_m(sensor[0], sensor[1])
                sensor[0]["n"] = simulator.get_n(sensor[0], sensor[0]["m"])
                lines.append(sensor)
        return lines

    def reset_head_status(self):
        for sensor in self.head_form:
            sensor["status"] = self.SENSOR_RANGE

    def send_sensor_data(self):
        for sensor in self.head_form:
            if sensor["status"] < self.SENSOR_RANGE:
                sensor["sensor"].write("distance=%f" % float)

"""
Datenhalter für Rauminformationen
"""
class room:
    waypoints = []

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
        file.close()

    """
    Liefert eine Liste von Strecken:
    (({"x": int, "y": int, "m": int, "n": int}, {"x": int, "y": int}), ...)
    """
    def get_lines(self):
        lines = ()
        max   = len(self.waypoints) - 1
        for i in range(len(self.waypoints)):
            line = (self.waypoints[i % max], self.waypoints[(i+1) % max])
            line[0]["m"] = simulator.get_m(line[0], line[1])
            line[0]["n"] = simulator.get_n(line[0], line[0]["m"])
            lines.append( line )
        return lines

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
        if not self.client.head_down:
            return 1

        client_pos = self.client.get_cur_position(now)
        self.client.reset_head_status()

        for line in self.room.get_lines():
            line[0]["m"] = get_m(line[0], line[1])
            line[0]["n"] = get_n(line[0], line[0]["m"])

            for sensor in self.client.get_head_lines():
                # Schnittpunkt
                # x = n1 - n2 / m2 - m1
                x_s = ( (line[0]["n"] - sensor[0]["n"])
                        / (sensor[0]["m"] - line[0]["m"]) )
                # y = ((m2 * n1) - (m1 * n2)) / (m2 - m1)
                y_s = ( (sensor[0]["m"] * line[0]["n"]
                         - sensor[0]["m"] * sensor[0]["n"])
                      / (sensor[0]["m"] - line[0]["m"]) )

                # jetzt der kürzeste Weg der Eckpunkte zur anderen Gerade
                # Schnittwinkel alpha
                alpha = math.degrees(abs(math.atan(m_line)
                                         - math.atan(sensor[0]["m"])))
                sensor[0]["s"] = get_s(sensor[0], x_s, y_s)
                sensor[1]["s"] = get_s(sensor[1], x_s, y_s)
                line[0]["s"]   = get_s(line[0]  , x_s, y_s)
                line[1]["s"]   = get_s(line[1]  , x_s, y_s)

                if in_comp(line[0]["s"], line[1]["s"],
                           get_lss(sensor[0]["s"], alpha)):
                    sensor[0]["status"] = min(sensor[0]["status"],
                                              get_hs(sensor[0]["s"], alpha))

                if in_comp(line[0]["s"], line[1]["s"],
                           get_lss(sensor[1]["s"], alpha)):
                    sensor[0]["status"] = min(sensor[0]["status"],
                                              get_hs(sensor[1]["s"], alpha))

                if in_comp(sensor[0]["s"], sensor[1]["s"],
                           get_lsl(line[0]["s"], alpha)):
                    sensor[0]["status"] = min(sensor[0]["status"],
                                              get_hl(line[0]["s"], alpha))

                if in_comp(sensor[0]["s"], sensor[1]["s"],
                           get_lsl(line[1]["s"], alpha)):
                    sensor[0]["status"] = min(sensor[0]["status"],
                                              get_hl(line[1]["s"], alpha))
        self.client.send_sensor_data()
        return 1

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



