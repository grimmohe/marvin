#!/usr/bin/env python
#coding=utf8

import os
import time
import string
import math
import pygame
import device

def get_angle(point1, point2={"x": 0, "y": 0}):
    """ git den Winkel einer Strecke in Radianten """
    x = point1["x"] - point2["x"]
    y = point1["y"] - point2["y"]
    factor = get_s({"x": x, "y": y})
    alpha = math.asin(abs(x) / factor)
    if y < 0:
        if x > 0:
            alpha = math.radians(180) - alpha
        else:
            alpha += math.radians(180)
    elif x < 0:
        alpha = math.radians(360) - alpha
    return alpha + math.radians(360) % math.radians(360) #immer positiver Winkel

def get_cutting_point(point1, point2):
    """ Schnittpunkt von 2 Geraden """
    out = None
    m1 = get_m(point1)
    m2 = get_m(point2)
    if m1 <> m2:
        n1 = get_n(point1, m1)
        n2 = get_n(point2, m2)
        out = {"x": (n1 - n2) / (m2 - m1),
               "y": ((m2 * n1) - (m1 * n2)) / (m2 - m1)}
    return out

def get_m(point):
    """ Steigungsfaktor """
    return math.tan(math.radians(90) - (point["a"] % math.radians(180)))

def get_n(point, m):
    """ Schnittpunkt (n) mit Y """
    return (point["y"] - m * point["x"])

def get_s(point1, point2={"x": 0, "y": 0}):
    """ Distanz von 2 Punkten """
    return math.sqrt( math.pow(point1["x"] - point2["x"], 2)
                      + math.pow(point1["y"] - point2["y"], 2) )

def get_hs(ss, angle):
    """ die Höhe auf dem Sensor """
    return math.tan(angle) * ss

def get_hl(sl, angle):
    """ die Höhe auf der Linie """
    return math.sin(angle) * sl

def get_lss(b, angle):
    """ Schnittpunkt von h auf linie """
    return b / math.cos(angle)

def get_lsl(c, angle):
    """ wie lss, nur von s von lien ausgehend """
    return math.cos(angle) * c

def in_comp(a1, a2, b):
    """ Vergleicht, ob b zwischen a1/a2 liegt """
    return min(a1, a2) < b < max(a1, a2)

def turn_point(point, degrees):
    """ Dreht einen Punkt auf der Systemachse """
    factor = get_s(point)
    alpha = get_angle(point) + math.radians(degrees)
    return { "x": round(math.sin(alpha) * factor, 5),
             "y": round(math.cos(alpha) * factor, 5) }

def max_point(point1, point2):
    """ Gibt den Point mit größerem X zurück """
    if point1["x"] > point2["x"]:
        bigger = point1
    else:
        bigger = point2
    return bigger

def min_point(point1, point2):
    """ Gibt den Point mit kleinerem X zurück """
    if point1["x"] < point2["x"]:
        smaler = point1
    else:
        smaler = point2
    return smaler

class Cleaner:
    """
    Representant für den Staubsauger
    """
    RADIUS         = 20.0
    SPEED          = 10.0 # 1/s
    SENSOR_RANGE   = 1.0
    CURVE_RADIUS   = 360 / (2 * math.pi)

    ACTION_HALTED     = 0
    ACTION_DRIVE      = 1
    ACTION_TURN_LEFT  = 2
    ACTION_TURN_RIGHT = 4

    head_form     = ( {"x": -20.0, "y":  0.0, "sensor": None, "id": "left",
                       "dev": "/tmp/dev_left",  "status": 1.0}
                    , {"x": -20.0, "y": 20.0, "sensor": None, "id": "front",
                       "dev": "/tmp/dev_front", "status": 1.0}
                    , {"x":  20.0, "y": 20.0, "sensor": None, "id": "right",
                       "dev": "/tmp/dev_right", "status": 1.0}
                    , {"x":  20.0, "y":  0.0, "sensor": None, "id": "",
                       "dev": "",               "status": 1.0} )
    head_down     = False
    head          = None
    engine        = None

    position      = {"x": 20.5, "y": 20.5}
    starttime     = 0.0
    action        = 0
    orientation   = 0.0

    def __init__(self):
        def cb_sensor_dummy(data): # auf diesen Devices wird nur gesendet
            pass
        for point in self.head_form:
            if len(point["dev"]) > 0:
                point["sensor"] = device.Device(point["dev"], cb_sensor_dummy, True)
        self.engine = device.Device('/tmp/dev_engine', self.cb_engine, True)
        self.head   = device.Device('/tmp/dev_head', self.cb_head, True)

    def __del__(self):
        self.head.close()
        self.head = None
        self.engine.close()
        self.engine = None
        for point in self.head_form:
            if point["sensor"] <> None:
                point["sensor"].close()
                point["sensor"] = None

    def cb_engine(self, data):
        """ Callback für die Motorsteuerung """
        data = string.split(data, "=")
        self.set_position(time.time())
        print "engine does: ", data
        if data[0] == "drive":
            if data[1] == "1":
                print "drive 1"
                self.action = (self.action | self.ACTION_DRIVE)
            else:
                print "drive n"
                self.action = self.ACTION_HALTED
        elif data[0] == "turn":
            if data[1] == "left":
                self.action = ((self.action | self.ACTION_TURN_LEFT)
                               & ~self.ACTION_TURN_RIGHT)
            elif data[1] == "right":
                self.action = ((self.action | self.ACTION_TURN_RIGHT)
                               & ~self.ACTION_TURN_LEFT)
            else:
                self.action = self.action & \
                              ~(self.ACTION_TURN_RIGHT | self.ACTION_TURN_LEFT)

    def cb_head(self, data):
        """ Callback für Saugkopf(/Head-)steuerung """
        data = string.split(data, "=")
        print "head does: ", data
        if data[0] == "move":
            if data[1] == "up":
                self.head_down = False
            elif data[1] == "down":
                self.head_down = True
            self.head.write("position=%s" % ["up", "down"][self.head_down])

    def set_position(self, current_time):
        """
        Setzt die eigene Position aus der Ursprungsposition, Ausrichtung und
        Bewegung als neue Ausgangslage.
        """
        self.position    = self.get_cur_position(current_time)
        self.orientation = self.get_cur_orientation(current_time)
        self.starttime   = current_time
        return 1

    def get_cur_orientation(self, current_time):
        """ Liefert die aktuelle Ausrichtung """
        diff = 0

        if self.action & (self.ACTION_TURN_LEFT | self.ACTION_TURN_RIGHT):
            diff = self.SPEED * (current_time - self.starttime)
            if self.action & self.ACTION_TURN_LEFT:
                diff = diff * -1

        return (self.orientation + diff) % 360

    def get_cur_position(self, current_time):
        """
        Berechnet die aktuelle Position aus Ursprungsposition, Ausrichtung und
        Bewegung.
        returns {"x": int, "y": int}
        """
        new_pos = {"x": self.position["x"],
                   "y": self.position["y"]}
        # TODO: Berechne eine Kurve mit self.CURVE_RADIUS
        if self.action & self.ACTION_DRIVE:
            orientation = math.radians(self.get_cur_orientation(current_time))
            distance = self.SPEED * (current_time - self.starttime)

            new_pos["x"] += math.sin(orientation) * distance
            new_pos["y"] += math.cos(orientation) * distance

        return new_pos

    def get_head_lines(self, current_time):
        """
        Liefert eine Liste von Strecken:
        (({"x": int, "y": int, "a": int}, {"x": int, "y": int}), ...)
        """
        lines = []
        if self.head_down:
            orientation = self.get_cur_orientation(current_time)
            cur_pos     = self.get_cur_position(current_time)
            max   = len(self.head_form)
            for i in range(len(self.head_form)):
                if self.head_form[i]["id"] <> "":
                    sensor = ( turn_point(self.head_form[i % max],
                                          orientation),
                               turn_point(self.head_form[(i+1) % max],
                                          orientation) )
                    sensor[0]["x"] += cur_pos["x"]
                    sensor[0]["y"] += cur_pos["y"]
                    sensor[1]["x"] += cur_pos["x"]
                    sensor[1]["y"] += cur_pos["y"]
                    sensor[0]["a"] = get_angle(sensor[0], sensor[1])
                    sensor[0]["o"] = self.head_form[i]
                    lines.append(sensor)
        return lines

    def reset_head_status(self):
        """ Setzt ded Sensorstatus auf das Maximum zurück """
        for sensor in self.head_form:
            sensor["status"] = self.SENSOR_RANGE

    def send_data(self, current_time):
        """ Schreibt die Sensordaten und Bewegungscounter """
        for sensor in self.head_form:
            if sensor["status"] < self.SENSOR_RANGE:
                sensor["sensor"].write("distance=%f" % sensor["status"])

        if self.action & self.ACTION_DRIVE:
            self.engine.write("distance=%f" % (self.SPEED * (current_time
                                                             - self.starttime)))
        if self.action & self.ACTION_TURN_RIGHT:
            self.engine.write("turn=%f" % (self.SPEED * (current_time
                                                         - self.starttime)))
        if self.action & self.ACTION_TURN_LEFT:
            self.engine.write("turn=%f" % (self.SPEED * (current_time
                                                         - self.starttime) * -1))

class Room:
    """
    Datenhalter für Rauminformationen
    """
    waypoints = []

    def __init__(self, wp_file):
        """
        Lädt eine Datei wp_file im Format x;y \n x;y
        Die Strecken von einem Punkt zum nächsten bilden die Wände des Raumen,
        in dem wir uns befinden.
        """
        self.waypoints = []
        self.loaded = False
        file = open(wp_file, "r")
        if not file:
            print "can't open file: ".wp_file

        for line in file.readlines():
            split = string.split(line, ";")
            self.waypoints.append({ "x": string.atoi(split[0])
                                  , "y": string.atoi(split[1]) })
        file.close()
        self.loaded = True

    def isValid(self):
        return self.loaded

    def get_lines(self):
        """
        Liefert eine Liste von Strecken:
        (({"x": int, "y": int, "a": int}, {"x": int, "y": int}), ...)
        """
        lines = []
        max   = len(self.waypoints)
        for i in range(len(self.waypoints)):
            line = (self.waypoints[i % max], self.waypoints[(i+1) % max])
            line[0]["a"] = get_angle(line[0], line[1])
            lines.append(line)
        return lines

class Simulator:
    """ Physiksimulator für den Client """
    runit          = False
    client         = None
    room           = None

    gui_height     = 1
    gui_y_offset   = 0
    gui_width      = 1
    gui_x_offset   = 0
    gui_factor     = 1
    GUI_MAX_SIZE   = 600
    gui_window     = None

    def __init__(self):
        self.client        = Cleaner()
        self.room          = Room("data/room.xy")

    def __del__(self):
        print "sim stop"

    def isValid(self):
        if not self.room.isValid():
            return False
        return True

    def check(self, now):
        """
        Die Kollisionsprüfung. Löst das Senden von Sensordaten aus.
        """
        client_pos = self.client.get_cur_position(now)
        self.client.reset_head_status()

        for line in self.room.get_lines():
            for sensor in self.client.get_head_lines(now):
                #Schnittpunkt berechnen
                cut = get_cutting_point(sensor[0], line[0])
                if cut:
                    # jetzt der kürzeste Weg der Eckpunkte zur anderen Gerade
                    # Schnittwinkel alpha
                    sensor[0]["s"] = get_s(sensor[0], cut)
                    sensor[1]["s"] = get_s(sensor[1], cut)
                    line[0]["s"]   = get_s(line[0]  , cut)
                    line[1]["s"]   = get_s(line[1]  , cut)

                    alpha = abs(math.atan(line[0]["a"])
                                - math.atan(sensor[0]["a"]))
                    if max(sensor[0]["s"], line[0]["s"]) > get_s(sensor[0], line[0]):
                        alpha = math.radians(180) - alpha

                    if in_comp(line[0]["s"], line[1]["s"],
                               get_lss(sensor[0]["s"], alpha)):
                        sensor[0]["o"]["status"] = min(sensor[0]["o"]["status"],
                                                  get_hs(sensor[0]["s"], alpha))

                    if in_comp(line[0]["s"], line[1]["s"],
                               get_lss(sensor[1]["s"], alpha)):
                        sensor[0]["o"]["status"] = min(sensor[0]["o"]["status"],
                                                  get_hs(sensor[1]["s"], alpha))

                    if in_comp(sensor[0]["s"], sensor[1]["s"],
                               get_lsl(line[0]["s"], alpha)):
                        sensor[0]["o"]["status"] = min(sensor[0]["o"]["status"],
                                                  get_hl(line[0]["s"], alpha))

                    if in_comp(sensor[0]["s"], sensor[1]["s"],
                               get_lsl(line[1]["s"], alpha)):
                        sensor[0]["o"]["status"] = min(sensor[0]["o"]["status"],
                                                  get_hl(line[1]["s"], alpha))
                else: # Parallel
                    # 0°
                    if sensor[0]["x"] == sensor[1]["x"]:
                        sensor[0]["o"]["status"] = min(sensor[0]["o"]["status"],
                                             abs(sensor[0]["x"] - line[0]["x"]))
                    # 180°
                    elif sensor[0]["y"] == sensor[1]["y"]:
                        sensor[0]["o"]["status"] = min(sensor[0]["o"]["status"],
                                             abs(sensor[0]["y"] - line[0]["y"]))
                    else:
                        # Formel aus Wikipedia (en)
                        a = get_s(sensor[0], sensor[1])
                        b = get_s(line[1], line[0])
                        c = get_s(min_point(sensor[0], sensor[1]),
                                  min_point(line[0], line[1]))
                        d = get_s(max_point(sensor[0], sensor[1]),
                                  max_point(line[0], line[1]))
                        h = math.sqrt((-a+b+c+d)*(a-b+c+d)*(a-b+c-d)*(a-b-c+d)/math.pow(2*(abs(b-a)), 2))

                        sensor[0]["o"]["status"] = min(sensor[0]["o"]["status"], h)


                self.client.send_data(now)
        self.client.send_data(now)
        return 1

    def init_gui(self):
        """
        Ermittelt das Ausmaß des Raumes, erstellt das Fenster und malt die Wände
        """
        for line in self.room.get_lines():
            for point in line:
                if point["y"] > 0:
                    self.gui_height = max(self.gui_height,
                                          point["y"] + self.gui_y_offset)
                if point["y"] < 0:
                    diff = max(0, abs(point["y"]) - self.gui_y_offset)
                    self.gui_y_offset += diff
                    self.gui_height   += diff

                if point["x"] > 0:
                    self.gui_width = max(self.gui_width,
                                         point["x"] + self.gui_x_offset)
                if point["x"] < 0:
                    diff = max(0, abs(point["x"]) - self.gui_x_offset)
                    self.gui_x_offset += diff
                    self.gui_width    += diff

        self.gui_factor = max(self.GUI_MAX_SIZE / self.gui_height,
                              self.GUI_MAX_SIZE / self.gui_width)
        # PyGame init stuff
        pygame.init()
        self.gui_window \
            = pygame.display.set_mode(((self.gui_width * self.gui_factor) + 1,
                                       (self.gui_height * self.gui_factor) + 1))
        pygame.display.set_caption("dust simulator")
        self.gui_window.fill((0, 0, 0))
        pygame.display.update()

    def update_gui(self, current_time):
        """ Zeichnet die grafische Ausgabe erneut """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.runit = False
        pos_alt = self.client.position
        pos_neu = self.client.get_cur_position(current_time)
        # Hintergrund füllen
        self.gui_window.fill((0, 0, 0))
        # die Wände zeichnen
        for line in self.room.get_lines():
            pygame.draw.line \
                ( self.gui_window,
                  (0, 0, 255),
                  ((line[0]["x"] + self.gui_x_offset) * self.gui_factor,
                   (line[0]["y"] + self.gui_y_offset) * self.gui_factor),
                  ((line[1]["x"] + self.gui_x_offset) * self.gui_factor,
                   (line[1]["y"] + self.gui_y_offset) * self.gui_factor),
                  1 )
        # die alte Position vor Beginn der Bewegung
        pygame.draw.circle \
            ( self.gui_window,
              (100, 100, 100),
              ((pos_alt["x"] + self.gui_x_offset) * self.gui_factor,
               (pos_alt["y"] + self.gui_y_offset) * self.gui_factor),
              self.client.RADIUS * self.gui_factor,
              1 )
        pygame.draw.line \
            ( self.gui_window,
              (100, 100, 100),
              ((pos_alt["x"] + self.gui_x_offset) * self.gui_factor,
               (pos_alt["y"] + self.gui_y_offset) * self.gui_factor),
              ((pos_neu["x"] + self.gui_x_offset) * self.gui_factor,
               (pos_neu["y"] + self.gui_y_offset) * self.gui_factor),
              1 )
        # die aktuelle Position
        pygame.draw.circle \
            ( self.gui_window,
              (0, 200, 0),
              ((pos_neu["x"] + self.gui_x_offset) * self.gui_factor,
               (pos_neu["y"] + self.gui_y_offset) * self.gui_factor),
              self.client.RADIUS * self.gui_factor,
              1 )
        # Saugkopf zeichnen
        for line in self.client.get_head_lines(current_time):
            pygame.draw.line \
                ( self.gui_window,
                  (0, 200, 0),
                  ((line[0]["x"] + self.gui_x_offset) * self.gui_factor,
                   (line[0]["y"] + self.gui_y_offset) * self.gui_factor),
                  ((line[1]["x"] + self.gui_x_offset) * self.gui_factor,
                   (line[1]["y"] + self.gui_y_offset) * self.gui_factor),
                  1 )
        pygame.display.update()

    def run(self):
        """ Main loop """
        self.init_gui()
        self.runit = True
        while self.runit:
            timestamp = time.time()
            # Kollisionskontrolle
            self.check(timestamp)
            # GUI
            self.update_gui(timestamp)
            # warten, aber bitte alle 0.01 aufwachen
            time.sleep(max(0, 0.01 - (time.time() - timestamp)))

# Und lauf!
if __name__ == '__main__':
    mysim = Simulator()
    if not mysim.isValid():
        print "sim is not valid"
    else:
        mysim.run()
        mysim = None
        print "It's done!"
        #TODO: quit() sollte nicht notwendig sein
    quit()


