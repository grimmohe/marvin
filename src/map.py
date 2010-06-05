#!/usr/bin/env python
#coding=utf8

class Point:
    
    def __init__(self):
        self.map=None
        self.x=0
        self.y=0
        
class Line:
    
    def __init__(self):
        self.begin=None
        self.end=None
        
    def connectLine(self, l):
        """ concenates single line """
        pass

    def connectLineList(self, ll):
        """ concenates a list of lines together and to thisline """
        pass
        
class Area:
    
    def __init__(self):
        self.lines=None

    def mergeArea(self, a):
        """ merge 2 areas together """
        pass
        
class Map:
    
    def __init__(self):
        self.areas=None
        self.lines=None
        self.points=None
        self.rasterSize=10
        self.extrapolateTreshold=2
        
    def addPoint(self, p):
        """ adding/merging a point to the map """
        pass
    
    def addLine(self, l):
        """ adding/merging a line to the map """ 
        pass
    
    def addArea(self, a):
        """ adding/merging an area to the map """
        pass

