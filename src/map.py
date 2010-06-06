#!/usr/bin/env python
#coding=utf8

""" global statics """
MERGE_RANGE = 10

class Vector:
    """
    point (X;Y) with size (X;Y)
    """
    def __init__(self, x, y, size_x, size_y):
        self.x = x
        self.y = y
        self.size_x = size_x
        self.size_y = size_y

    def startPoint(self):
        return (self.x, self.y)

    def endPoint(self):
        return (self.x + self.size_x, self.y + self.size_y)

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
        self.extrapolateThreshold = 2

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
        aa = 0
        max = len(self.vectors)
        while ii < max:
            v1 = self.vectors[ii]
            while aa < max:
                if ii == aa:
                    continue
                v2 = self.vectors[aa]
                #TODO: jetzt prüfen, ob die nicht vielleicht zusammengeführt werden können
