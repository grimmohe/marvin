#!/usr/bin/env python
#coding=utf8

import math
from numpy.ma.core import max
from mathix import turn_point, roundup, getVectorIntersectionRatio, get_angle
from common import SortedList

""" global statics """
MERGE_RANGE = 1.0
MAX_VECTOR_LENGTH = 50.0
MAX_RANGE = 6378137000

class Point(object):

    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)

    def getDistanceTo(self, p2):
        return math.sqrt(math.pow(self.x - p2.x, 2) + math.pow(self.y - p2.y, 2))

    def getTurned(self, angle):
        p = turn_point({"x": self.x, "y": self.y}, angle)
        return Point(p["x"], p["y"])

class WayPoint(Point):

    WP_STRICT = 1           # get there, stay on a direkt way as much as possible
    WP_FAST = 2             # get there on a short way
    WP_DISCOVER = 4         # discover the loose end you are on

    def __init__(self, x, y, duty=WP_FAST, attachment=None):
        super(WayPoint, self).__init__(x, y)
        self.duty = duty
        self.attachment = attachment

class Position:

    def __init__(self, point=Point(0, 0), orientation=0.0):
        self.point = point
        self.orientation = orientation

class Vector:

    START_POINT = 0
    END_POINT = 1

    """
    point (X;Y) with size (X;Y)
    """
    def __init__(self, point=Point(0, 0), size=Point(0, 0)):
        self.point = point
        self.size = size

    def combine(self, vector1, vector2, kind_of_point):
        """ create a new vector between vector1 and vector2 """
        if kind_of_point == Vector.START_POINT:
            p1x = vector1.point.x
            p1y = vector1.point.y
            p2x = vector2.point.x
            p2y = vector2.point.y
        elif kind_of_point == Vector.END_POINT:
            p1x = vector1.point.x + vector1.size.x
            p1y = vector1.point.y + vector1.size.y
            p2x = vector2.point.x + vector2.size.x
            p2y = vector2.point.y + vector2.size.y
        return Vector(Point(p1x, p1y), Point(p2x - p1x, p2y - p1y))

    def copy(self, position=Point(0, 0), orientation=0, offset=None):
        """ create a new vector with position added and orientation applied to size """
        x = self.point.x
        y = self.point.y
        if offset:
            x += offset.size.x
            y += offset.size.y
        new_pos = turn_point({"x": x, "y": y}, orientation)
        new_size = turn_point({"x": self.size.x, "y": self.size.y}, orientation)
        return Vector(Point(new_pos["x"] + position.x, new_pos["y"] + position.y),
                      Point(new_size["x"], new_size["y"]))

    def getAngle(self):
        return math.degrees(get_angle({"x": self.size.x, "y": self.size.y}))

    def getStartPoint(self):
        return Point(self.point.x, self.point.y)

    def getEndPoint(self):
        return Point(self.point.x + self.size.x, self.point.y + self.size.y)

    def len(self):
        return math.sqrt(math.pow(abs(self.size.x), 2) + math.pow(abs(self.size.y), 2))

    def compare(self, v):
        s1 = self.getStartPoint()
        e1 = self.getEndPoint()
        s2 = v.getStartPoint()
        e2 = v.getEndPoint()
        p1 = math.sqrt(math.pow(s1.x - s2.x, 2) + math.pow(s1.y - s2.y, 2))
        p2 = math.sqrt(math.pow(s1.x - e2.x, 2) + math.pow(s1.y - e2.y, 2))
        p3 = math.sqrt(math.pow(e1.x - s2.x, 2) + math.pow(e1.y - s2.y, 2))
        p4 = math.sqrt(math.pow(e1.x - e2.x, 2) + math.pow(e1.y - e2.y, 2))
        return (p1, p2, p3, p4)

    def distance(self, v):
        c = self.compare(v)
        return min(c[0], min(c[1], min(c[2], c[3])))

    def inRange(self, v):
        comp = self.compare(v)
        return (comp[0] <= MERGE_RANGE or comp[1] <= MERGE_RANGE,
                comp[2] <= MERGE_RANGE or comp[3] <= MERGE_RANGE)

    def isConnected(self, v):
        comp = self.compare(v)
        if comp[0] <= MERGE_RANGE or comp[1] <= MERGE_RANGE \
        or comp[2] <= MERGE_RANGE or comp[3] <= MERGE_RANGE :
            return True
        ratio = getVectorIntersectionRatio(self, v)
        if ratio and 0 <= ratio[0] <= 1:
            p = self.getStartPoint()
            p.x += self.size.x * ratio[0]
            p.y += self.size.y * ratio[0]
            if p.getDistanceTo(v.getStartPoint()) <= MERGE_RANGE \
            or p.getDistanceTo(v.getEndPoint()) <= MERGE_RANGE:
                return True
        if ratio and 0 <= ratio[1] <= 1:
            p = v.getStartPoint()
            p.x += v.size.x * ratio[1]
            p.y += v.size.y * ratio[1]
            if p.getDistanceTo(self.getStartPoint()) <= MERGE_RANGE \
            or p.getDistanceTo(self.getEndPoint()) <= MERGE_RANGE:
                return True
        return False

    def merge(self, v):
        comp = self.compare(v)
        max_dist = 0.0
        max_index = 0
        for ii in range(4):
            if comp[ii] > max_dist:
                max_dist = comp[ii]
                max_index = ii
        if max_index == 0:
            self.setStartPoint(self.getStartPoint())
            self.setEndPoint(v.getStartPoint())
        elif max_index == 1:
            self.setStartPoint(self.getStartPoint())
            self.setEndPoint(v.getEndPoint())
        elif max_index == 2:
            self.setStartPoint(self.getEndPoint())
            self.setEndPoint(v.getStartPoint())
        elif max_index == 3:
            self.setStartPoint(self.getEndPoint())
            self.setEndPoint(v.getEndPoint())

    def setStartPoint(self, p):
        e = self.getEndPoint()
        self.point = Point(p.x, p.y)
        self.setEndPoint(e)

    def setEndPoint(self, p):
        self.size = Point(p.x - self.point.x, p.y - self.point.y)

    def twist(self):
        p1 = self.point
        p2 = self.getEndPoint()
        self.setStartPoint(p2)
        self.setEndPoint(p1)

class BorderList:

    def __init__(self):
        self.borders = []

    def add(self, v=Vector()):
        if v and v.__class__.__name__ == "Vector":
            distance = v.len()
            max = roundup(distance / MAX_VECTOR_LENGTH)
            for run in range(max):
                multiplier = run / max
                point = Point(v.point.x + (v.size.x * multiplier), v.point.y + (v.size.y * multiplier))
                size = Point(v.size.x / max, v.size.y / max)
                self.borders.append(Vector(point, size))
        else:
            raise "Object None or wrong type. Expected Vector()"

    def getAllBorders(self):
        ret = []
        for b in self.borders:
            ret.append(b)
        return ret

    def getBordersInRange(self, x1=-MAX_RANGE, y1=-MAX_RANGE, x2=MAX_RANGE, y2=MAX_RANGE):
        x1, x2, y1, y2 = sorted([x1, x2]) + sorted([y1, y2])
        ret = []
        for border in self.borders:
            if x1 <= border.point.x <= x2 and y1 <= border.point.y <= y2 \
            or x1 <= border.point.x + border.size.x <= x2 and y1 <= border.point.y + border.size.y <= y2:
                ret.append(border)
        return ret

    def getConnectedBorders(self, border=Vector()):
        """ returns borders within MERGE_RANGE """
        con = []
        for v in self.borders:
            if v <> border and border.isConnected(v):
                con.append(v)
        return con

    def getLooseEnds(self, position=Position()):
        """ find loose ends in self.borders, sorted by distace to position  """
        ii = 0
        looseEnds = []
        while ii < len(self.borders):
            v = self.borders[ii]
            aa = 0
            loose = [True, True]
            while (loose[0] or loose[1]) and aa < len(self.borders):
                if ii <> aa:
                    range = v.inRange(self.borders[aa])
                    loose[0] = loose[0] and not range[0]
                    loose[1] = loose[1] and not range[1]
                aa += 1
            if loose[0]:
                v.twist()
            if loose[0] or loose[1]:
                looseEnds.append(v)
            ii += 1
        looseEnds.sort(cmp=lambda v1, v2: int(position.point.getDistanceTo(v1.point) - position.point.getDistanceTo(v2.point)))
        return looseEnds

    def getLooseEndPoints(self, border=Vector()):
        """ identify if start or end point of border is loose """
        ret = []
        sp = border.getStartPoint()
        if len(self.getBordersInRange(sp.x - MERGE_RANGE,
                                      sp.y - MERGE_RANGE,
                                      sp.x + MERGE_RANGE,
                                      sp.y + MERGE_RANGE)) < 2:
            ret.append(sp)
        ep = border.getEndPoint()
        if len(self.getBordersInRange(ep.x - MERGE_RANGE,
                                      ep.y - MERGE_RANGE,
                                      ep.x + MERGE_RANGE,
                                      ep.y + MERGE_RANGE)) < 2:
            ret.append(ep)
        return ret


    def remove(self, v):
        self.borders.remove(v)

class Area:
    """
    Triangle of Points
    """

    def __init__(self, p1, p2, p3):
        self.p1 = p1
        self.p2 = p2
        self.p3 = p3

    def intersects(self, vector):
        """ returns True, if vector is intersecting or within the area """
        size12 = Point(self.p2.x - self.p1.x, self.p2.y - self.p1.y)
        size13 = Point(self.p3.x - self.p1.x, self.p3.y - self.p1.y)
        size23 = Point(self.p3.x - self.p2.x, self.p3.y - self.p2.y)

        ratio12 = getVectorIntersectionRatio(Vector(self.p1, size12), vector)
        ratio13 = getVectorIntersectionRatio(Vector(self.p1, size13), vector)
        ratio23 = getVectorIntersectionRatio(Vector(self.p2, size23), vector)

        intersecting = False

        if ratio12 and ratio13 and 0<=ratio12[0]<=1 and 0<=ratio13[0]<=1:
            intersecting = (0<=ratio12[1]<=1
                            or
                            0<=ratio13[1]<=1
                            or
                            ((ratio12[1]<0) <> (ratio13[1]<0)))
        if ratio23 and 0<=ratio23[0]<=1 and ratio12 and 0<=ratio12[0]<=1:
            intersecting = (intersecting
                            or
                            0<=ratio23[1]<=1
                            or
                            0<=ratio12[1]<=1
                            or
                            ((ratio23[1]<0) <> (ratio12[1]<0)))
        if ratio23 and 0<=ratio23[0]<=1 and ratio13 and 0<=ratio13[0]<=1:
            intersecting = (intersecting
                            or
                            0<=ratio23[1]<=1
                            or
                            0<=ratio13[1]<=1
                            or
                            ((ratio23[1]<0) <> (ratio13[1]>0)))

        return intersecting

class Router:

    def __init__(self, objectRadius=0):
        self.waypoints = SortedList(lambda a, b: id(a) - id(b))
        self.objectRadius = objectRadius

    def _addWaypoint(self, b1=Vector(), b2=Vector()):
        ratio = getVectorIntersectionRatio(b1, b2)
        if ratio:
            collision = Point(b1.point.x + b1.size.x * ratio[0], b1.point.y + b1.size.y * ratio[0])
            if b1.point.getDistanceTo(collision) > b1.size.getDistanceTo(collision):
                b1.twist()
            if b2.point.getDistanceTo(collision) > b2.size.getDistanceTo(collision):
                b2.twist()
            ba1 = b1.getAngle()
            ba2 = b2.getAngle()
            wa1 = (ba1 + ba2) / 2
            wa2 = (wa1 + 180) % 360
            if wa1 > 0:
                self.waypoints.append(self._getWPPosition(collision, min(ba1, ba2), wa1))
            if wa2 > 0:
                self.waypoints.append(self._getWPPosition(collision, min(ba1, ba2), wa2))

    def _getWPPosition(self, collision, ba, wa):
        angle = abs(ba - wa) % 90
        c = self.objectRadius * math.sin(math.radians(angle))
        p = turn_point({"x": 0, "y": c}, wa)
        return Point(collision.x + p["x"], collision.y + p["y"])

    def discover(self, position, direction, cb_addAction):
        """
        direction is a Vector(), the loose end of a border.
        it has to discover in direction of the start point.
        """
        pass

    def prepare(self, borders=BorderList()):
        """ generate waypoints """
        self.waypoints.clear()
        finishedBorders = SortedList(lambda a, b: id(a) - id(b))
        for border in borders.getAllBorders():
            if finishedBorders.contains(border):
                continue
            finishedBorders.append(border)
            for c in borders.getConnectedBorders(border):
                if finishedBorders.contains(c):
                    continue
                self._addWaypoint(border, c)
            for p in borders.getLooseEndPoints(border):
                if border.point.getDistanceTo(p) > 0:
                    border.twist()
                self._addWaypoint(border, Vector(p, border.size.getTurned(90)))
                self._addWaypoint(border, Vector(p, border.size.getTurned(-90)))

    def route(self, position=Position(), destination=WayPoint(), cb_addAction):
        pass

class Map:

    def __init__(self):
        self.areas = []
        self.areas_unmerged = []
        self.borders = BorderList()
        self.waypoints = []

    def addArea(self, p1, p2, p3):
        """
        Adding/merging an area to the map.
        We expect p1 to be connected to p2 and p3 rectangular.
        """
        def getTweenPoint(root, size1, size2, multi1, multi2):
            return Point(root.x + (size1.x * multi1) + (size2.x * multi2),
                         root.y + (size2.y * multi2) + (size2.y * multi2))
        def appendWhereNeeded(area):
            self.areas.append(area)
            self.areas_unmerged.append(area)

        distance12 = p1.getDistanceTo(p2)
        distance13 = p1.getDistanceTo(p3)
        max12 = roundup(distance12 / MAX_VECTOR_LENGTH)
        max13 = roundup(distance13 / MAX_VECTOR_LENGTH)
        size12 = Point(p2.x - p1.x, p2.y - p1.y)
        size13 = Point(p3.x - p1.x, p3.y - p1.y)
        for run12 in range(max12):
            multiplierMin12 = run12 / max12
            multiplierMax12 = (run12 + 1) / max12
            for run13 in range(max13):
                multiplierMin13 = run13 / max13
                multiplierMax13 = (run13 + 1) / max13
                appendWhereNeeded(Area(getTweenPoint(p1, size12, size13, multiplierMin12, multiplierMin13),
                                       getTweenPoint(p1, size12, size13, multiplierMin12, multiplierMax13),
                                       getTweenPoint(p1, size12, size13, multiplierMax12, multiplierMin13)))
                appendWhereNeeded(Area(getTweenPoint(p1, size12, size13, multiplierMax12, multiplierMax13),
                                       getTweenPoint(p1, size12, size13, multiplierMin12, multiplierMax13),
                                       getTweenPoint(p1, size12, size13, multiplierMax12, multiplierMin13)))

    def addWaypoint(self, wp=WayPoint(0, 0)):
        """ add a waypoint to current waypoints """
        self.waypoints.append(wp)

    def nextCollisionIn(self, position=Position(), sensors=[], min_distance=0):
        """ calc distance to next collision """
        nextCollision = MAX_RANGE
        collisionSensor = None
        direction = turn_point({"x": 0, "y": 1}, position.orientation)
        direction = Point(direction["x"], direction["y"])

        for sensor in sensors:
            v1 = Vector(sensor.getStartPoint().getTurned(position.orientation), direction)
            v2 = Vector(sensor.getEndPoint().getTurned(position.orientation), direction)
            for border in self.borders.getAllBorders():
                ratio1 = getVectorIntersectionRatio(v1, border)
                ratio2 = getVectorIntersectionRatio(v2, border)
                if ratio1 and ratio2 \
                   and ( 0 <= ratio1[1] <= 1 or 0 <= ratio2[1] <= 1 or ((ratio1[1]>=0) <> (ratio2[1]>=0)) ) \
                   and min(ratio1[0], ratio2[0]) >= min_distance:
                    nextCollision = min(nextCollision, min(ratio1[0], ratio2[0]))
                    collisionSensor = sensor
        return (nextCollision, collisionSensor)

    def merge(self):
        """ merge borders that could be one """
        ii = 0
        doubleMax = MAX_VECTOR_LENGTH * 2
        borders = self.borders.getAllBorders()
        while ii < len(borders):
            v1 = borders[ii]
            aa = ii + 1
            while aa < len(borders):
                v2 = borders[aa]
                max_dist = 0.0
                count_in_range = 0
                for distance in v1.compare(v2):
                    max_dist = max(max_dist, distance)
                    if distance <= MERGE_RANGE:
                        count_in_range += 1
                # die Vektoren liegen übereinander
                if count_in_range == 2:
                    self.borders.remove(borders.pop(aa))
                # die Vektoren bilden eine Linie
                elif (count_in_range == 1
                      and (v1.len() + v2.len() - max_dist <= MERGE_RANGE)
                      and max_dist < MAX_VECTOR_LENGTH):
                    v1.merge(v2)
                    self.borders.remove(borders.pop(aa))
                else:
                    aa += 1
            ii += 1
        """ now delete all borders in conflict with self.areas_unmerged """
        while len(self.areas_unmerged):
            area = self.areas_unmerged[0]
            ii = 0
            while ii < len(self.borders):
                vector = self.borders[ii]
                if area.p1.getDistanceTo(vector.point) > doubleMax:
                    ii += 1
                    continue
                if area.intersects(vector):
                    self.borders.remove(borders.pop(ii))
                else:
                    ii += 1
            self.areas_unmerged.pop(0)

    def routeIsSet(self):
        return len(self.waypoints)

