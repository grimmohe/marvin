#!/usr/bin/env python
#coding=utf8

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
    try:
        alpha = math.asin(abs(x) / factor)
    except ZeroDivisionError:
        alpha = 0.0
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
    """ wie turn_pointr, aber in grad """
    return turn_pointr(point, math.radians(degrees))

def turn_pointr(point, rad):
    """ Dreht einen Punkt auf der Systemachse """
    factor = get_s(point)
    alpha = get_angle(point) + rad
    return { "x": round(math.sin(alpha) * factor, 5),
             "y": round(math.cos(alpha) * factor, 5) }

def max_point(point1, point2):
    """ Gibt den Point mit größerem y zurück """
    if point1["y"] > point2["y"]:
        bigger = point1
    else:
        bigger = point2
    return bigger

def min_point(point1, point2):
    """ Gibt den Point mit kleinerem y zurück """
    if point1["y"] < point2["y"]:
        smaler = point1
    else:
        smaler = point2
    return smaler

def within(p1, p2, s):
    """ liegt der Schnittpunkt im Bereich des Vektors? """
    lreturn = ( s["x"] > min(p1["x"], p2["x"])
                and
                s["x"] < max(p1["x"], p2["x"])
                and
                s["y"] > min(p1["y"], p2["y"])
                and
                s["y"] < max(p1["y"], p2["y"]))
    return lreturn

def getVectorIntersectionRatio(v1, v2, v3):
    """
    v1 = (bx1;by1)
    v2 = (bx2;by2)
    v3 = (bx3;by3)

    dp1 = -by3*bx2 + bx3*by2
    dp2 = -by1*bx2 + bx1*by2

    rat = dp1/dp2
    """
    try:
        return ( (-v3["y"]*v2["x"] + v3["x"]*v2["y"])
                 / (-v1["y"]*v2["x"] + v1["x"]*v2["y"]) )
    except ZeroDivisionError:
        return None # parallel

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

    def __init__(self):
        self.head_form     = ( {"x": -20.0, "y":  0.0, "sensor": None, "id": "left",
                                "status": 1.0}
                             , {"x": -20.0, "y": 20.0, "sensor": None, "id": "front",
                                "status": 1.0}
                             , {"x":  20.0, "y": 20.0, "sensor": None, "id": "right",
                                "status": 1.0}
                             , {"x":  20.0, "y":  0.0, "sensor": None, "id": "",
                                "status": 1.0} )
        self.head_down     = False
        self.head          = None
        self.engine        = None

        self.position      = {"x": 20.5, "y": 20.5}
        self.starttime     = 0.0
        self.action        = 0
        self.orientation   = 0.0

        def cb_sensor_dummy(data): # auf diesen Devices wird nur gesendet
            pass
        for point in self.head_form:
            if len(point["id"]) > 0:
                point["sensor"] = device.Device(point["id"], cb_sensor_dummy)
        self.engine = device.Device('engine', self.cb_engine)
        self.head   = device.Device('head', self.cb_head)

    def __del__(self):
        self.head.close()
        self.head = None
        self.engine.close()
        self.engine = None
        for point in self.head_form:
            if point["sensor"] <> None:
                point["sensor"].close()
                point["sensor"] = None

    def reset(self):
        self.head_down     = False
        self.position      = {"x": 20.5, "y": 20.5}
        self.starttime     = 0.0
        self.action        = 0
        self.orientation   = 0.0

    def cb_engine(self, data):
        """ Callback für die Motorsteuerung """
        data = string.split(data, "=")
        if data[0] == "drive":
            self.set_position(time.time())
            if data[1] == "1":
                print "drive 1"
                self.action = (self.action | self.ACTION_DRIVE)
            else:
                print "drive n"
                self.action = self.ACTION_HALTED
        elif data[0] == "turn":
            self.set_position(time.time())
            if data[1] == "left":
                self.action = ((self.action | self.ACTION_TURN_LEFT)
                               & ~self.ACTION_TURN_RIGHT)
            elif data[1] == "right":
                self.action = ((self.action | self.ACTION_TURN_RIGHT)
                               & ~self.ACTION_TURN_LEFT)
            else:
                self.action = self.action & \
                              ~(self.ACTION_TURN_RIGHT | self.ACTION_TURN_LEFT)
        elif data[0] == "reset":
            self.reset()

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
          Ursprung              Vektor
        (({"x": int, "y": int}, {"x": int, "y": int}), ...)
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
                                          orientation),
                               {"x": 0.0, "y": 0.0} )
                    sensor[0]["x"] += cur_pos["x"]
                    sensor[0]["y"] += cur_pos["y"]
                    sensor[1]["x"] += cur_pos["x"]
                    sensor[1]["y"] += cur_pos["y"]
                    sensor[2]["x"] = sensor[1]["x"] - sensor[0]["x"]
                    sensor[2]["y"] = sensor[1]["y"] - sensor[0]["y"]
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
          Ursprung              Vektor
        (({"x": int, "y": int}, {"x": int, "y": int}), ...)
        """
        lines = []
        max   = len(self.waypoints)
        for i in range(len(self.waypoints)):
            point1 = self.waypoints[i % max]
            point2 = self.waypoints[(i+1) % max]
            vector = {"x": point2["x"] - point1["x"],
                      "y": point2["y"] - point1["y"]}
            line = (point1, point2, vector)
            lines.append(line)
        return lines

    def get_size(self):
        min_x = 0
        max_x = 0
        min_y = 0
        max_y = 0

        for point in self.waypoints:
            min_x = min(min_x, point["x"])
            max_x = max(max_x, point["x"])
            min_y = min(min_y, point["y"])
            max_y = max(max_y, point["y"])

        return {"x": -min_x + max_x,
                "y": -min_y + max_y}


class Simulator:
    """
    Physiksimulator für den Client
    """

    def __init__(self):
        self.runit          = False
        self.client         = None
        self.room           = None

        self.gui_height     = 1
        self.gui_y_offset   = 0
        self.gui_width      = 1
        self.gui_x_offset   = 0
        self.gui_window     = None

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
        self.client.reset_head_status()

        for line in self.room.get_lines():
            for sensor_o in self.client.get_head_lines(now):
                status = 1.0
                vector_ratio = ( math.pow(sensor_o[2]["x"], 2)
                                 / (math.pow(sensor_o[2]["x"], 2)
                                    + math.pow(sensor_o[2]["y"], 2)) )
                for range in [0.0, .2, -.2, .4, -.4, .6, -.6, .8, -.8, 1.0, -1.0]:
                    if status < 1.0:
                        break
                    # Sensor um range verschieben
                    x = math.sqrt(range * range * vector_ratio)
                    y = math.sqrt(range * range * (1 - vector_ratio))
                    if sensor_o[2]["x"] > 0:
                        y = -y
                    if sensor_o[2]["y"] > 0:
                        x = -x
                    if range < .0:
                        x = -x
                        y = -y
                    sensor = ({"x": sensor_o[0]["x"]+x, "y": sensor_o[0]["y"]+y},
                              {"x": sensor_o[1]["x"]+x, "y": sensor_o[1]["y"]+y},
                              {"x": sensor_o[2]["x"],   "y": sensor_o[2]["y"]})

                    v3 = {"x": line[0]["x"] - sensor[0]["x"],
                          "y": line[0]["y"] - sensor[0]["y"]}
                    ratio = getVectorIntersectionRatio(sensor[2], line[2], v3)
                    if ratio:
                        intersection = {"x": sensor[2]["x"]*ratio,
                                        "y": sensor[2]["y"]*ratio}
                        if ( within(sensor[0], sensor[1], intersection)
                             and
                             within(line[0], line[1], intersection) ):
                            # direkter Schnitt
                            status = max(0, abs(range - .1))
                    elif range == 0.0:
                        # Parallel
                        # Drehen
                        angle = - get_angle(sensor[0], sensor[1])
                        l1 = (turn_pointr(sensor[0], angle),
                              turn_pointr(sensor[1], angle))
                        l2 = (turn_pointr(line[0], angle),
                              turn_pointr(line[1], angle))
                        # Jetzt ist X bei beiden Punkten einer Linie gleich
                        # Überschneiden sich die Linien auf Y?
                        if (min(l1[0]["y"], l1[1]["y"]) < max(l2[0]["y"], l2[1]["y"])
                            and
                            max(l1[0]["y"], l1[1]["y"]) > min(l2[0]["y"], l2[1]["y"])):
                            status = abs(l1[0]["x"] - l2[0]["x"])

                sensor_o[0]["o"]["status"] = min(sensor_o[0]["o"]["status"], status)
        self.client.send_data(now)
        return 1

    def init_gui(self):
        """
        Initialisiert das PyGame Fenster
        """
        pygame.init()
        self.gui_window = pygame.display.set_mode((200, 200), pygame.RESIZABLE)
        pygame.display.set_caption("dust simulator")
        self.gui_window.fill((0, 0, 0))
        pygame.display.update()

    def update_gui(self, current_time):
        """ Zeichnet die grafische Ausgabe erneut """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.runit = False
            elif event.type == pygame.VIDEORESIZE:
                self.gui_window = pygame.display.set_mode(event.size, pygame.RESIZABLE)

        pos_alt = self.client.position
        pos_neu = self.client.get_cur_position(current_time)

        room_size = self.room.get_size()
        screen_size_x, screen_size_y = self.gui_window.get_size()
        screen_size_x -= 1
        screen_size_y -= 1
        factor = min(float(screen_size_x) / room_size["x"], float(screen_size_y) / room_size["y"])

        # Hintergrund füllen
        self.gui_window.fill((0, 0, 0))
        # die Wände zeichnen
        for line in self.room.get_lines():
            pygame.draw.line \
                ( self.gui_window,
                  (0, 0, 255),
                  ((line[0]["x"] + self.gui_x_offset) * factor,
                   (line[0]["y"] + self.gui_y_offset) * factor),
                  ((line[1]["x"] + self.gui_x_offset) * factor,
                   (line[1]["y"] + self.gui_y_offset) * factor),
                  1 )
        # die alte Position vor Beginn der Bewegung
        pygame.draw.circle \
            ( self.gui_window,
              (100, 100, 100),
              (int((pos_alt["x"] + self.gui_x_offset) * factor),
               int((pos_alt["y"] + self.gui_y_offset) * factor)),
              int(self.client.RADIUS * factor),
              1 )
        pygame.draw.line \
            ( self.gui_window,
              (100, 100, 100),
              ((pos_alt["x"] + self.gui_x_offset) * factor,
               (pos_alt["y"] + self.gui_y_offset) * factor),
              ((pos_neu["x"] + self.gui_x_offset) * factor,
               (pos_neu["y"] + self.gui_y_offset) * factor),
              1 )
        # die aktuelle Position
        pygame.draw.circle \
            ( self.gui_window,
              (0, 200, 0),
              (int((pos_neu["x"] + self.gui_x_offset) * factor),
               int((pos_neu["y"] + self.gui_y_offset) * factor)),
              int(self.client.RADIUS * factor),
              1 )
        # Saugkopf zeichnen
        for line in self.client.get_head_lines(current_time):
            pygame.draw.line \
                ( self.gui_window,
                  (0, 200, 0),
                  ((line[0]["x"] + self.gui_x_offset) * factor,
                   (line[0]["y"] + self.gui_y_offset) * factor),
                  ((line[1]["x"] + self.gui_x_offset) * factor,
                   (line[1]["y"] + self.gui_y_offset) * factor),
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


