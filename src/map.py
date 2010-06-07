#!/usr/bin/env python
#coding=utf8

import math
from numpy.ma.core import max

""" global statics """
MERGE_RANGE = 1

class Vector:
    """
    point (X;Y) with size (X;Y)
    """
    def __init__(self, x, y, size_x, size_y):
        self.x = x
        self.y = y
        self.size_x = size_x
        self.size_y = size_y

    def getStartPoint(self):
        return (self.x, self.y)

    def getEndPoint(self):
        return (self.x + self.size_x, self.y + self.size_y)

    def len(self):
        return math.sqrt(math.pow(abs(self.size_x), 2) + math.pow(abs(self.size_y), 2))

    def compare(self, v):
        s1 = self.getStartPoint()
        e1 = self.getEndPoint()
        s2 = v.getStartPoint()
        e2 = v.getEndPoint()
        p1 = math.sqrt(math.pow(s1[0] - s2[0], 2) + math.pow(s1[1] - s2[1], 2))
        p2 = math.sqrt(math.pow(s1[0] - e2[0], 2) + math.pow(s1[1] - e2[1], 2))
        p3 = math.sqrt(math.pow(e1[0] - s2[0], 2) + math.pow(e1[1] - s2[1], 2))
        p4 = math.sqrt(math.pow(e1[0] - e2[0], 2) + math.pow(e1[1] - e2[1], 2))
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
        self.x = p[0]
        self.y = p[1]

    def setEndPoint(self, p):
        self.size_x = p[0] - self.x
        self.size_y = p[1] - self.y

class Area:
    """
    Closed ring of vectors
    """

    def __init__(self):
        self.vectors = None
        self.finished = False

    def hasVactor(self, v):
        """ check availability of vector v in self.vectors """
        return (v in self.vectors)

class Map:

    def __init__(self):
        self.areas = None
        self.vectors = []

    def addVector(self, v):
        """ adding/merging a point to the map """
        if v and v.__class__.__name__ == "Vector":
            self.vectors.add(v)
        else:
            raise "Object None or wrong type. Expected Vector()"

    def addArea(self, a):
        """ adding/merging an area to the map """
        pass

    def merge(self):
        """ merge vectors that could be one """
        ii = 0
        max_len = len(self.vectors)
        while ii < max_len:
            v1 = self.vectors[ii]
            aa = ii + 1
            while aa < max_len:
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
                    max_len -= 1
                # die Vektoren bilden eine Linie
                elif count_in_range == 1 and (v1.len() + v2.len() - max_dist <= MERGE_RANGE):
                    v1.merge(v2)
                    self.vectors.pop(aa)
                    max_len -= 1







