#!/usr/bin/env python
#coding=utf8

import math

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

def get_s(point1, point2={"x": 0, "y": 0}):
    """ Distanz von 2 Punkten """
    return math.sqrt( math.pow(point1["x"] - point2["x"], 2)
                      + math.pow(point1["y"] - point2["y"], 2) )

def turn_point(point, degrees):
    """ wie turn_pointr, aber in grad """
    return turn_pointr(point, math.radians(degrees))

def turn_pointr(point, rad):
    """ Dreht einen Punkt auf der Systemachse """
    factor = get_s(point)
    alpha = get_angle(point) + rad
    return { "x": round(math.sin(alpha) * factor, 5),
             "y": round(math.cos(alpha) * factor, 5) }

def getVectorIntersectionRatioSim(v1, v2, v3):
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

def getVectorIntersectionRatio(v1, v2):
    """
    v1, v2, v3 = map.Point()

    dp1 = -by3*bx2 + bx3*by2
    dp2 = -by1*bx2 + bx1*by2

    rat = dp1/dp2

    returns (ratio on v1, ratio on v2)
    if 0<=ratio<=1 its an intersection
    """

    def getPRatio(p1, p2, mid):
        return (-mid[1]*p2.x + mid[0]*p2.y) / (-p1.y*p2.x + p1.x*p2.y)

    mid1 = (v1.point.x - v2.point.x, v1.point.y - v2.point.y)
    mid2 = (v2.point.x - v1.point.x, v2.point.y - v1.point.y)

    try:
        return (getPRatio(v1.size, v2.size, mid2),
                getPRatio(v2.size, v1.size, mid1))
    except ZeroDivisionError:
        return None # parallel

def roundup(n):
    """ round up, always! """
    down = math.trunc(n)
    if n - down > 0:
        down += 1
    return down
