#!/usr/bin/env python
#coding=utf8

import math
from numpy.ma.core import max
from mathix import turn_point, roundup, getVectorIntersectionRatio

""" global statics """
MERGE_RANGE = 1.0
MAX_VECTOR_LENGTH = 50.0

class Point:

    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)

    def getDistanceTo(self, p2):
        return math.sqrt(math.pow(self.x - p2.x, 2) + math.pow(self.y - p2.y, 2))

class Vector:

    START_POINT = 0
    END_POINT = 1

    """
    point (X;Y) with size (X;Y)
    """
    def __init__(self, point, size):
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

    def copy(self, position=Point(0, 0), orientation=0):
        """ create a new vector with position added and orientation applied to size """
        new_pos = turn_point({"x": self.x, "y": self.y}, orientation)
        new_size = turn_point({"x": self.size_x, "y": self.size_y}, orientation)
        return Vector(Point(new_pos["x"] + position.x, new_pos["y"] + position.y),
                      Point(new_size["x"], new_size["y"]))

    def getStartPoint(self):
        return Point(self.point.x, self.point.y)

    def getEndPoint(self):
        return Point(self.x + self.size_x, self.y + self.size_y)

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
        self.point = Point(p.x, p.y)

    def setEndPoint(self, p):
        self.size = Point(p.x - self.point.x, p.y - self.point.y)

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

class Map:

    ROUTE_STRICT = 1
    ROUTE_SHORT = 2

    def __init__(self):
        self.areas = []
        self.areas_unmerged = []
        self.vectors = []
        self.route = []

    def addVector(self, v):
        """ adding/merging a point to the map """
        if v and v.__class__.__name__ == "Vector":
            distance = v.len()
            max = roundup(distance / MAX_VECTOR_LENGTH)
            for run in range(max):
                multiplier = run / max
                point = Point(v.point.x + (v.size.x * multiplier), v.point.y + (v.size.y * multiplier))
                size = Point(v.size.x / max, v.size.y / max)
                self.vectors.append(Vector(point, size))
        else:
            raise "Object None or wrong type. Expected Vector()"

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

    def addWaypoint(self, wp=Point(0, 0), option=Map.ROUTE_STRICT):
        """ add a waypoint to current route """

    def fill(self):
        """ generetes a route to fill noticeable areas"""
        return False

    def merge(self):
        """ merge vectors that could be one """
        ii = 0
        doubleMax = MAX_VECTOR_LENGTH * 2
        while ii < len(self.vectors):
            v1 = self.vectors[ii]
            aa = ii + 1
            while aa < len(self.vectors):
                v2 = self.vectors[aa]
                max_dist = 0.0
                count_in_range = 0
                for distance in v1.compare(v2):
                    max_dist = max(max_dist, distance)
                    if distance <= MERGE_RANGE:
                        count_in_range += 1
                # die Vektoren liegen übereinander
                if count_in_range == 2:
                    self.vectors.pop(aa)
                # die Vektoren bilden eine Linie
                elif (count_in_range == 1
                      and (v1.len() + v2.len() - max_dist <= MERGE_RANGE)
                      and max_dist < MAX_VECTOR_LENGTH):
                    v1.merge(v2)
                    self.vectors.pop(aa)
                else:
                    aa += 1
            ii += 1
        """ now delete all vectors in conflict with self.areas_unmerged """
        while len(self.areas_unmerged):
            area = self.areas_unmerged[0]
            ii = 0
            while ii < len(self.vectors):
                vector = self.vectors[ii]
                if area.p1.getDistanceTo(vector.point) > doubleMax:
                    ii += 1
                    continue
                if area.intersects(vector):
                    self.vectors.pop(ii)
                else:
                    ii += 1
            self.areas_unmerged.pop(0)

    def routeIsSet(self):
        return len(self.route)

