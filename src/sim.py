#!/usr/bin/env python
#coding=utf8

import os
import time
import string
import math
import pygame
import device

def get_m(point1, point2={"x": 0, "y": 0}):
    """ Steigungsfaktor """
    return ( (point1["y"] - point2["y"])
             / (point1["x"] - point2["x"] + 0.000001) )

def get_n(point, m):
    """ Schnittpunkt (n) mit Y """
    return (point["y"] - m * point["x"])

def get_s(point1, point2={"x": 0, "y": 0}):
    """ Distanz von 2 Punkten """
    return math.sqrt( math.pow(point1["x"] - point2["x"], 2)
                      + math.pow(point1["y"] - point2["y"], 2) )

def get_hs(ss, angle):
    """ die Höhe auf dem Sensor """
    return math.tan(math.radians(angle)) * ss

def get_hl(sl, angle):
    """ die Höhe auf der Linie """
    return math.sin(math.radians(angle)) * sl

def get_lss(b, angle):
    """ Schnittpunkt von h auf linie """
    return b / math.cos(math.radians(angle))

def get_lsl(c, angle):
    """ wie lss, nur von s von lien ausgehend """
    return math.cos(math.radians(angle)) * c

def in_comp(a1, a2, b):
    """ Vergleicht, ob b zwischen a1/a2 liegt """
    return min(a1, a2) < b < max(a1, a2)

def turn_point(point, degrees):
    """ Dreht einen Punkt auf der Systemachse """
    s = get_s(point)
    alpha = math.atan(get_m(point)) + math.radians(degrees)
    return { "x": s * math.sin(alpha),
             "y": s * math.cos(alpha) }

class Cleaner:
    """
    Representant für den Staubsauger
    """
    RADIUS         = 20.0
    SPEED          = 10.0 # 1/s
    SENSOR_RANGE   = 1.0
    CURVE_RADIUS   = 360 / (2 * math.pi)

    ACTION_DRIVE      = 1
    ACTION_TURN_LEFT  = 2
    ACTION_TURN_RIGHT = 4

    head_form     = ( {"x": -10.0, "y":  0.0, "sensor": None, "id": "left",
                       "dev": "/tmp/dev_left",  "status": 1.0}
                    , {"x": -10.0, "y": 10.0, "sensor": None, "id": "front",
                       "dev": "/tmp/dev_front", "status": 1.0}
                    , {"x":  10.0, "y": 10.0, "sensor": None, "id": "right",
                       "dev": "/tmp/dev_right", "status": 1.0}
                    , {"x":  10.0, "y":  0.0, "sensor": None, "id": "",
                       "dev": "",               "status": 1.0} )
    head_down     = False
    head          = None
    engine        = None

    position      = {"x": 20.0, "y": 20.0}
    starttime     = 0.0
    action        = 0
    orientation   = 0.0

    def __init__(self):
        def cb_sensor_dummy(data): # auf diesen Devices wird nur gesendet
            pass
        for point in self.head_form:
            if len(point["dev"]) > 0:
                point["sensor"] = device.Device(point["dev"], cb_sensor_dummy)
        self.engine = device.Device('/tmp/dev_engine', self.cb_engine)
        self.head   = device.Device('/tmp/dev_head', self.cb_head)

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
            if data[1] == "1\n":
                print "drive 1"
                self.action = (self.action | self.ACTION_DRIVE)
            else:
                print "drive n"
                self.action = (self.action ^ self.ACTION_DRIVE)
        elif data[0] == "turn":
            if data[1] == "left":
                self.action = ((self.action | self.ACTION_TURN_LEFT)
                               ^ self.ACTION_TURN_RIGHT)
            elif data[1] == "right":
                self.action = ((self.action | self.ACTION_TURN_RIGHT)
                               ^ self.ACTION_TURN_LEFT)
            else:
                self.action = ((self.action ^ self.ACTION_TURN_RIGHT)
                               ^ self.ACTION_TURN_LEFT)

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
                diff = 360 - diff

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
            distance = self.SPEED * (current_time - self.starttime)

            # c = distance
            # Alpha = orientation MOD 90°
            # also Sin Alpha = a/c -> a = Sin Alpha * c
            # und  Cos Altha = b/c -> b = Cos Alpha * c
            orientation = self.get_cur_orientation(current_time)
            alpha = math.radians(orientation % 90)
            a = math.sin(alpha) * distance
            b = math.cos(alpha) * distance

            part = round(orientation / 90)
            if part == 0:
                new_pos["x"] += a
                new_pos["y"] += b
            elif part == 1:
                new_pos["x"] += b
                new_pos["y"] += a
            elif part == 2:
                new_pos["x"] += a
                new_pos["y"] += b
            elif part == 3:
                new_pos["x"] += b
                new_pos["y"] += a

        return new_pos

    def get_head_lines(self, current_time):
        """
        Liefert eine Liste von Strecken:
        (({"x": int, "y": int, "m": int, "n": int}, {"x": int, "y": int}), ...)
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
                    sensor[0]["m"] = get_m(sensor[0], sensor[1])
                    sensor[0]["n"] = get_n(sensor[0], sensor[0]["m"])
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
            self.engine.write("distance=%f" % self.SPEED * int(current_time
                                                            - self.starttime))
        if self.action & self.ACTION_TURN_RIGHT:
            self.engine.write("turn=%f" % int(self.SPEED) * int(current_time
                                                        - self.starttime ))
        if self.action & self.ACTION_TURN_LEFT:
            self.engine.write("turn=%f" % self.SPEED * int(current_time
                                                        - self.starttime) * -1)

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
        (({"x": int, "y": int, "m": int, "n": int}, {"x": int, "y": int}), ...)
        """
        lines = []
        max   = len(self.waypoints)
        for i in range(len(self.waypoints)):
            line = (self.waypoints[i % max], self.waypoints[(i+1) % max])
            line[0]["m"] = get_m(line[0], line[1])
            line[0]["n"] = get_n(line[0], line[0]["m"])
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
        Die eigentliche Kollisionsprüfung. Löst das Senden von Sensordaten aus.
        """
        client_pos = self.client.get_cur_position(now)
        self.client.reset_head_status()

        for line in self.room.get_lines():
            line[0]["m"] = get_m(line[0], line[1])
            line[0]["n"] = get_n(line[0], line[0]["m"])

            for sensor in self.client.get_head_lines(now):
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
                sensor[0]["s"] = get_s(sensor[0], {"x": x_s, "y": y_s})
                sensor[1]["s"] = get_s(sensor[1], {"x": x_s, "y": y_s})
                line[0]["s"]   = get_s(line[0]  , {"x": x_s, "y": y_s})
                line[1]["s"]   = get_s(line[1]  , {"x": x_s, "y": y_s})

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
        self.gui_window = pygame.display.set_mode( ((self.gui_width * self.gui_factor) + 1,
                                                    (self.gui_height * self.gui_factor) + 1) )
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


