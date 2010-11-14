#!/usr/bin/env python
#coding=utf8

import time
import string
import math
import pygame
import device
from mathix import get_angle, turn_point, turn_pointr, getVectorIntersectionRatioSim

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

        self.head          = None
        self.engine        = None

        self.reset()

        def cb_sensor_dummy(data): # auf diesen Devices wird nur gesendet
            pass
        for point in self.head_form:
            if len(point["id"]) > 0:
                point["sensor"] = device.Device(point["id"], cb_sensor_dummy)
        self.engine = device.Device('engine', self.cb_engine)
        self.head   = device.Device('head', self.cb_head)

    def __del__(self):
        self.quit()

    def quit(self):
        self.head.close()
        self.head = None
        self.engine.close()
        self.engine = None
        for point in self.head_form:
            if point["sensor"]:
                point["sensor"].close()
                point["sensor"] = None

    def reset(self):
        self.head_down     = False
        self.position      = {"x": 20.5, "y": 20.5}
        self.starttime     = 0.0
        self.action        = 0
        self.orientation   = 0.0
        for sensor in self.head_form:
            sensor["status"] = 1.0

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
                print "turn left"
                self.action = self.ACTION_TURN_LEFT
            elif data[1] == "right":
                print "turn right"
                self.action = self.ACTION_TURN_RIGHT
            else:
                print "turn stop"
                self.action = self.ACTION_HALTED
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
                sensor["sensor"].write("distance=%.2f" % sensor["status"])

        if self.action & self.ACTION_DRIVE:
            self.engine.write("distance=%f" % (self.SPEED * (current_time
                                                             - self.starttime)))
        if self.action & self.ACTION_TURN_RIGHT:
            self.engine.write("turned=%f" % (self.SPEED * (current_time
                                                           - self.starttime)))
        if self.action & self.ACTION_TURN_LEFT:
            self.engine.write("turned=%f" % (self.SPEED * (current_time
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

    def __del__(self):
        self.quit()

    def quit(self):
        self.waypoints = None

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
        self.gui_size_x     = 1
        self.gui_y_offset   = 0
        self.gui_size_y     = 1
        self.gui_x_offset   = 0
        self.gui_factor     = 1
        self.gui_window     = None

        self.runit          = False

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
            for sensor in self.client.get_head_lines(now):
                status = self.checkSensorStatus(sensor, line)

                sensor[0]["o"]["status"] = min(sensor[0]["o"]["status"], status)
        self.client.send_data(now)
        return 1

    def checkSensorStatus(self, sensor, line):
        status = 1.0

        v1 = {"x": line[0]["x"] - sensor[0]["x"],
              "y": line[0]["y"] - sensor[0]["y"]}
        v2 = {"x": sensor[0]["x"] - line[0]["x"],
              "y": sensor[0]["y"] - line[0]["y"]}
        ratio1 = getVectorIntersectionRatioSim(sensor[2], line[2], v1)
        ratio2 = getVectorIntersectionRatioSim(line[2], sensor[2], v2)

        if ratio1 and ratio2:
            if (0 <= ratio1 <= 1) and (0 <= ratio2 <= 1):
                # direkter Schnitt
                status = 0
            else:
            # Drehen
                angle = - get_angle(sensor[0], sensor[1])
                s = (turn_pointr(sensor[0], angle),
                     turn_pointr(sensor[1], angle))
                l = (turn_pointr(line[0], angle),
                     turn_pointr(line[1], angle))
                # nachdem s eine x-steigung von 0 hat, müssen sich die vektoren nur auf y schneiden
                if (min(s[0]["y"], s[1]["y"]) < max(l[0]["y"], l[1]["y"])
                    and
                    max(s[0]["y"], s[1]["y"]) > min(l[0]["y"], l[1]["y"])):
                    # was über steht kommt weg
                    # nur x wird danach ausgewertet
                    if l[0]["y"] > s[0]["y"]:
                        l[0]["x"] += (l[1]["x"] - l[0]["x"]) / (l[1]["y"] - l[0]["y"]) * (l[0]["y"] - s[0]["y"])
                    if l[1]["y"] > s[0]["y"]:
                        l[1]["x"] += (l[0]["x"] - l[1]["x"]) / (l[0]["y"] - l[1]["y"]) * (l[1]["y"] - s[0]["y"])

                    if l[0]["y"] < s[1]["y"]:
                        l[0]["x"] += (l[1]["x"] - l[0]["x"]) / (l[1]["y"] - l[0]["y"]) * (l[0]["y"] - s[1]["y"])
                    if l[1]["y"] < s[1]["y"]:
                        l[1]["x"] += (l[0]["x"] - l[1]["x"]) / (l[0]["y"] - l[1]["y"]) * (l[1]["y"] - s[1]["y"])

                    status = min(min(abs(s[0]["x"] - l[0]["x"]),
                                     abs(s[1]["x"] - l[0]["x"])),
                                 min(abs(s[0]["x"] - l[1]["x"]),
                                     abs(s[1]["x"] - l[1]["x"])))
        else:
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

        return status

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
        self.gui_size_x, self.gui_size_y = self.gui_window.get_size()
        self.gui_size_x -= 1
        self.gui_size_y -= 1
        self.gui_factor = min(float(self.gui_size_x) / room_size["x"], float(self.gui_size_y) / room_size["y"])

        # Hintergrund füllen
        self.gui_window.fill((0, 0, 0))
        # die Wände zeichnen
        for line in self.room.get_lines():
            pygame.draw.line \
                ( self.gui_window,
                  (0, 0, 255),
                  self.point(line[0]["x"], line[0]["y"]),
                  self.point(line[1]["x"], line[1]["y"]),
                  1 )
        # die alte Position vor Beginn der Bewegung
        pygame.draw.circle \
            ( self.gui_window,
              (100, 100, 100),
              self.point(pos_alt["x"],pos_alt["y"]),
              int(self.client.RADIUS * self.gui_factor),
              1 )
        pygame.draw.line \
            ( self.gui_window,
              (100, 100, 100),
              self.point(pos_alt["x"], pos_alt["y"]),
              self.point(pos_neu["x"], pos_neu["y"]),
              1 )
        # die aktuelle Position
        pygame.draw.circle \
            ( self.gui_window,
              (0, 200, 0),
              self.point(pos_neu["x"], pos_neu["y"]),
              int(self.client.RADIUS * self.gui_factor),
              1 )
        # Saugkopf zeichnen
        for line in self.client.get_head_lines(current_time):
            pygame.draw.line \
                ( self.gui_window,
                  (0, 200, 0),
                  self.point(line[0]["x"], line[0]["y"]),
                  self.point(line[1]["x"], line[1]["y"]),
                  1 )
        # systeminformationen ausgeben
        font = pygame.font.SysFont("Arial", 10)
        posY = 10
        for s in self.client.head_form:
            if s["id"]:
                text = "%0s: %1f" % (s["id"], s["status"])
                text = font.render(text, 1, (255, 255, 255))
                self.gui_window.blit(text, (10, posY))
                posY += 15

        text = "orientation: %0f" % (self.client.get_cur_orientation(current_time))
        text = font.render(text, 1, (255, 255, 255))
        self.gui_window.blit(text, (10, posY))

        pygame.display.update()

    def point(self, x, y):
        x = int((x + self.gui_x_offset) * self.gui_factor)
        y = self.gui_size_y - int((y + self.gui_y_offset) * self.gui_factor)
        return (x, y)

    def run(self):
        """ Main loop """
        try:
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
        except KeyboardInterrupt:
            pass
        pygame.quit()
        self.client.quit()
        self.room.quit()

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


