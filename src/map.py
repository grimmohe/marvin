#!/usr/bin/env python
#coding=utf8

import math
from numpy.ma.core import max
from mathix import turn_point, roundup, getVectorIntersectionRatio, get_angle,\
    getVectorToPointDistance
from common import SortedList, Enumerator
import xmltemplate

""" global statics """
MERGE_RANGE = 1.0
MAX_VECTOR_LENGTH = 50.0
MAX_RANGE = 6378137000

def isAngle(a):
    return a and type(1) in (int, float)

def angleIsFront(a):
    return isAngle(a) and (a >= 315 or a <= 45)

def angleIsLeft(a):
    return isAngle(a) and a >= 225 and a <= 315

def angleIsRight(a):
    return isAngle(a) and a >= 45 and a <= 135

class Point(object):

    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)

    def add(self, point):
        self.x += point.x
        self.y += point.y

    def copy(self):
        return Point(self.x, self.y)

    def getDistanceTo(self, p2):
        return math.sqrt(math.pow(self.x - p2.x, 2) + math.pow(self.y - p2.y, 2))

    def getTurned(self, angle):
        p = turn_point({"x": self.x, "y": self.y}, angle)
        return Point(p["x"], p["y"])

class WayPoint(Point):

    WP_STRICT = 1           # get there, stay on a direkt way as much as possible
    WP_FAST = 2             # get there on a short way
    WP_DISCOVER = 4         # discover the loose end you are on

    def __init__(self, x=0, y=0, duty=WP_FAST, attachment=None):
        super(WayPoint, self).__init__(x, y)
        self.duty = duty
        self.attachment = attachment

class Position:

    def __init__(self, point=Point(0, 0), orientation=0.0):
        self.point = point
        self.orientation = orientation

    def copy(self):
        return Position(Point(self.point.x, self.point.y), self.orientation)

    def getPointInDistance(self, distance):
        p = Point(0, distance).getTurned(self.orientation)
        p.x += self.point.x
        p.y += self.point.y
        return p

class Vector:

    START_POINT = 0
    END_POINT = 1

    """
    point (X;Y) with size (X;Y)
    """
    def __init__(self, point=Point(0, 0), size=Point(0, 0), endPoint=None):
        self.point = point
        self.size = size
        if endPoint:
            self.setEndPoint(endPoint)

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
        v = Vector(self.point.copy(), self.size.copy())

        if offset:
            v.point.x += offset.size.x
            v.point.y += offset.size.y

        if orientation:
            v = Vector(v.point.getTurned(orientation), v.size.getTurned(orientation))

        if position:
            v.point.x += position.x
            v.point.y += position.y

        return v

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

    def compareGetMaxMin(self, v):
        c = self.compare(v)
        iMax = c.index(max(c)) #index of max distance
        if iMax == 0:
            return (self.getStartPoint(), v.getStartPoint(), self.getEndPoint(), v.getEndPoint())
        elif iMax == 1:
            return (self.getStartPoint(), v.getEndPoint(), self.getEndPoint(), v.getStartPoint())
        elif iMax == 2:
            return (self.getEndPoint(), v.getStartPoint(), self.getStartPoint(), v.getEndPoint())
        elif iMax == 3:
            return (self.getEndPoint(), v.getEndPoint(), self.getStartPoint(), v.getStartPoint())

    def distanceMin(self, v):
        c = self.compare(v)
        return min(c[0], min(c[1], min(c[2], c[3])))

    def distanceMax(self, v):
        c = self.compare(v)
        return max(c[0], max(c[1], max(c[2], c[3])))

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
        """ combine th 2 most distant points into this vector """
        comp = self.compare(v)
        max_dist = 0.0
        max_index = 0
        for ii in range(4):
            if comp[ii] > max_dist:
                max_dist = comp[ii]
                max_index = ii
        if self.len() > comp[max_index]:
            pass
        elif max_index == 0:
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

class VectorList:

    def __init__(self):
        self.vectors = []

    def __len__(self):
        return self.count()

    def __getitem__(self, index):
        return self.get(index)

    def add(self, v=Vector()):
        if v and v.__class__.__name__ == "Vector":
            distance = v.len()
            max = roundup(distance / MAX_VECTOR_LENGTH)
            for run in range(max):
                multiplier = float(run) / max
                point = Point(v.point.x + (v.size.x * multiplier), v.point.y + (v.size.y * multiplier))
                size = Point(v.size.x / max, v.size.y / max)
                self.vectors.append(Vector(point, size))
        else:
            raise "Object None or wrong type. Expected Vector()"

    def count(self):
        return len(self.vectors)

    def get(self, index):
        return self.vectors[index]

    def getAllVectors(self):
        ret = []
        for b in self.vectors:
            ret.append(b)
        return ret

    def getVectorsInRange(self, x1=-MAX_RANGE, y1=-MAX_RANGE, x2=MAX_RANGE, y2=MAX_RANGE):
        x1, x2, y1, y2 = sorted([x1, x2]) + sorted([y1, y2])
        ret = []
        for vector in self.vectors:
            if x1 <= vector.point.x <= x2 and y1 <= vector.point.y <= y2 \
            or x1 <= vector.point.x + vector.size.x <= x2 and y1 <= vector.point.y + vector.size.y <= y2:
                ret.append(vector)
        return ret

    def getConnectedVectors(self, vector=Vector()):
        """ returns vectors within MERGE_RANGE """
        con = []
        for v in self.vectors:
            if v <> vector and vector.isConnected(v):
                con.append(v)
        return con

    def getLooseEnds(self, position=Position()):
        """ find loose ends in self.vectors, sorted by distace to position  """
        ii = 0
        looseEnds = []
        while ii < len(self.vectors):
            v = self.vectors[ii]
            aa = 0
            loose = [True, True]
            while (loose[0] or loose[1]) and aa < len(self.vectors):
                if ii <> aa:
                    range = v.inRange(self.vectors[aa])
                    loose[0] = loose[0] and not range[0]
                    loose[1] = loose[1] and not range[1]
                aa += 1
            if loose[0]:
                v.twist()
            if loose[0] or loose[1]:
                looseEnds.append(v)
            ii += 1
        looseEnds.sort(cmp=lambda v1, v2: int(position.point.getDistanceTo(v1.getEndPoint())
                                              - position.point.getDistanceTo(v2.getEndPoint())))
        return looseEnds

    def getLooseEndPoints(self, vector=Vector()):
        """ identify if start or end point of vector is loose """
        ret = []
        sp = vector.getStartPoint()
        if len(self.getVectorsInRange(sp.x - MERGE_RANGE,
                                      sp.y - MERGE_RANGE,
                                      sp.x + MERGE_RANGE,
                                      sp.y + MERGE_RANGE)) < 2:
            ret.append(sp)
        ep = vector.getEndPoint()
        if len(self.getVectorsInRange(ep.x - MERGE_RANGE,
                                      ep.y - MERGE_RANGE,
                                      ep.x + MERGE_RANGE,
                                      ep.y + MERGE_RANGE)) < 2:
            ret.append(ep)
        return ret

    def index(self, v):
        return self.vectors.index(v)

    def remove(self, v):
        self.vectors.remove(v)

class Router:

    def __init__(self, objectRadius=0):
        self.waypoints = SortedList(lambda a, b: id(a) - id(b))
        self.routes = SortedList(self.__routesOrder)
        self.objectRadius = objectRadius
        self.shortest = None

    def __routesOrder(self, a, b):
        order = a["left"] - b["left"]
        if not order:
            order = a["distance"] - b["distance"]
        if not order:
            order = len(a["wp"]) - len(b["wp"])
        return order

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

    def actionDiscover(self, position, directionVector, cb_getSensorList, cb_addAction):
        """
        direction is a Vector(), the loose end of a border.
        it has to discover in direction of the start point.
        """
        turned = False
        direction = xmltemplate.DIRECTION_LEFT
        if directionVector:
            ratio = getVectorIntersectionRatio(Vector(position.point,
                                                      Point(0, 1).getTurned(position.orientation)),
                                               directionVector)
            if ratio and ratio[0] > 0:
                self.actionTurn(position,
                                goAngle=180,
                                cb_getSensorList=cb_getSensorList,
                                cb_addAction=cb_addAction)
                turned = True

            a1 = Vector(position.point, endPoint=directionVector.getStartPoint()).getAngle()
            a2 = Vector(position.point, endPoint=directionVector.getEndPoint()).getAngle()
            if not(a1 > a2 or abs(a1-a2) > 180):
                direction = xmltemplate.DIRECTION_RIGHT
        sensors = cb_getSensorList(position)
        sensorsTouching = []
        sensorsUntouched = []
        for s in sensors:
            a = (Vector(endPoint=s.getStartPoint()).getAngle() + Vector(endPoint=s.getEndPoint()).getAngle()) / 2
            if (direction == xmltemplate.DIRECTION_LEFT and angleIsLeft(a)) \
            or (direction == xmltemplate.DIRECTION_RIGHT and angleIsRight(a)):
                sensorsTouching.append(s.name)
            else:
                sensorsUntouched.append(s.name)
        if turned:
            cb_addAction(xmltemplate.TEMPLATE_TURN_HIT,
                         direction=direction,
                         baseSensor=sensorsTouching,
                         untouchedSensor=[])

        cb_addAction(xmltemplate.TEMPLATE_DISCOVER,
                     direction=direction,
                     baseSensor=sensorsTouching,
                     untouchedSensor=sensorsUntouched)

    def actionDrive(self, position, distance=None, cb_getSensorList=None, cb_addAction=None):
        if not (cb_getSensorList and cb_addAction):
            raise Exception("cb_getSensorList or cb_addAction missing")
        sensorsUntouched = []
        if distance:
            for s in cb_getSensorList():
                sensorsUntouched.append(s.name)
        else:
            for s in cb_getSensorList():
                a = (Vector(endPoint=s.getStartPoint()).getAngle() + Vector(endPoint=s.getEndPoint()).getAngle() / 2)
                if angleIsFront(a):
                    sensorsUntouched.append(s.name)
        cb_addAction(xmltemplate.TEMPLATE_DRIVE,
                     untouchedSensor=sensorsUntouched,
                     distance=distance)

    def actionHead(self, headUp, cb_addAction):
        if headUp:
            movement = xmltemplate.HEAD_UP
        else:
            movement = xmltemplate.HEAD_DOWN
        cb_addAction(xmltemplate.TEMPLATE_HEAD,
                     headMovement=movement)

    def actionRoute(self, position, destination, cb_getSensorList, cb_addAction, cb_getCollisions):
        """
        finds a route from position to destination. cb_addAction is used to transfer required
        client actions into templates and later assignments.
        """
        self._actionRouteRun(position, destination, cb_getSensorList, cb_getCollisions)

        if self.routes.count():
            route = self.routes.get(0)
            for wp in route["wp"]:
                self.actionTurn(position=position,
                                destAngle=Vector(position.point, endPoint=wp).getAngle(),
                                cb_getSensorList=cb_getSensorList,
                                cb_addAction=cb_addAction)
                self.actionDrive(position=position,
                                 distance=position.point.getDistanceTo(wp),
                                 cb_getSensorList=cb_getSensorList,
                                 cb_addAction=cb_addAction)

        self.routes.clear()

    def _actionRouteRun(self, position, destination, cb_getSensorList, cb_getCollisions, route={"distance": 0, "wp": [], "left": None}):
        """ run through all possible waypoints to find destination """

        def copyRoute(route):
            return {"distance": route["distance"],
                    "wp": [] + route["wp"],
                    "left": route["left"]}
        position = position.copy()
        basicSensor = Vector(Point(-self.objectRadius, 0), Point(self.objectRadius*2, 0))
        for index in range(self.waypoints.count()):
            wp = self.waypoints.get(index)
            if not route["wp"].count(wp): # not two times the same waypoint
                position.orientation = Vector(position.point, endPoint=wp).getAngle()
                distance = cb_getCollisions(position, basicSensor)
                if len(distance):
                    distanceC = distance[0][0]
                else:
                    distanceC = MAX_RANGE
                distanceWP = position.point.getDistanceTo(wp)
                if distanceC >= distanceWP:
                    r = copyRoute(route)
                    r["distance"] += distanceWP
                    r["wp"].append(wp)
                    position.point = wp
                    self._actionRouteRun(position, destination, cb_getSensorList, cb_getCollisions, r)

        position.orientation = Vector(position.point, endPoint=destination).getAngle()
        #TODO: the collisions comming out of here are bullshit
        distance = cb_getCollisions(position, cb_getSensorList(True))
        if len(distance):
            distanceC = distance[0]
        else:
            distanceC = (position.point.getDistanceTo(destination), None, destination)
        distanceWP = position.point.getDistanceTo(destination)
        route["wp"].append(distanceC[2])
        route["distance"] += distanceC[0]
        route["left"] = distanceC[2].getDistanceTo(destination)
        self.routes.append(route)


    def actionTurn(self, position, goAngle=None, destAngle=None,
                   hitSensorNames=None, hitDirection=None, cb_getSensorList=None, cb_addAction=None):
        """
        turn the device to a destined or relative angle while the head is up or not.
        maybe you turn and turn till you hit something.
        """
        if not (cb_getSensorList and cb_addAction):
            raise Exception("cb_getSensorList or cb_addAction missing")

        if hitSensorNames or hitDirection:
            if not (hitSensorNames and hitDirection):
                raise Exception()
            sensors = cb_getSensorList()
            sensorsTouching = []
            sensorsUntouched = []
            for s in sensors:
                a = (Vector(endPoint=s.getStartPoint()).getAngle() + Vector(endPoint=s.getEndPoint()).getAngle() / 2)
                if (hitDirection == xmltemplate.DIRECTION_LEFT and angleIsLeft(a)) \
                or (hitDirection == xmltemplate.DIRECTION_RIGHT and angleIsRight(a)):
                    sensorsTouching.append(s.name)
                else:
                    sensorsUntouched.append(s.name)
            cb_addAction(xmltemplate.TEMPLATE_TURN_HIT,
                         baseSensor=sensorsTouching,
                         untouchedSensor=sensorsUntouched,
                         direction=hitDirection)
            if goAngle:
                position.orientation += goAngle
            if destAngle:
                position.orientation = destAngle
        else:
            if not (position and (goAngle <> None or destAngle <> None)):
                raise Exception()

            direction = xmltemplate.DIRECTION_LEFT
            if goAngle:
                destAngle = position.orientation + goAngle
                if goAngle > 0: direction = xmltemplate.DIRECTION_RIGHT
            else:
                goAngle = (360 + destAngle - position.orientation) % 360
                if goAngle > 180:
                    goAngle -= 360
                    direction = xmltemplate.DIRECTION_LEFT

            cb_addAction(xmltemplate.TEMPLATE_HEAD,
                         headMovement=xmltemplate.HEAD_UP)

            cb_addAction(xmltemplate.TEMPLATE_TURN_ANGLE,
                         direction=direction,
                         targetAngle=goAngle)

            cb_addAction(xmltemplate.TEMPLATE_HEAD,
                         headMovement=xmltemplate.HEAD_DOWN)

    #TODO: prepare is never called
    def prepare(self, borders=VectorList()):
        """ generate waypoints """
        self.waypoints.clear()
        finishedBorders = SortedList(lambda a, b: id(a) - id(b))
        for border in borders.getAllVectors():
            if finishedBorders.contains(border):
                continue
            finishedBorders.append(border)
            for c in borders.getConnectedVectors(border):
                if finishedBorders.contains(c):
                    continue
                self._addWaypoint(border, c)
            for p in borders.getLooseEndPoints(border):
                if border.point.getDistanceTo(p) > 0:
                    border.twist()
                self._addWaypoint(border, Vector(p, border.size.getTurned(90)))
                self._addWaypoint(border, Vector(p, border.size.getTurned(-90)))

class Map:

    def __init__(self):
        self.driven = VectorList()
        self.borders = VectorList()
        self.waypoints = []
        self.moveStartPosition = None

    def addWaypoint(self, wp=WayPoint(0, 0)):
        """ add a waypoint to current waypoints """
        self.waypoints.append(wp)

    def clearWaypoints(self):
        self.waypoints = []

    def addDrive(self, start, end):
        """ add a Vector() drive way """
        self.driven.add(Vector(start.copy(), endPoint=end.copy()))

    def getCollisions(self, position=Position(), sensors=[], min_distance=0):
        """ calc distance to next collision """
        def __order(a, b):
            if a[0] - b[0] > 0:
                return 1
            else:
                return -1

        collisions = []
        direction = Point(0, 1).getTurned(position.orientation)
        odirection = Point(0, -1).getTurned(position.orientation)

        positionedSensors = []
        for s in sensors:
            positionedSensors.append((s, s.copy(position.point, position.orientation)))

        borders = self.borders.getAllVectors()
        for border in borders:
            distance = MAX_RANGE
            sensedby = None
            for sensor in positionedSensors:
                # sensor direction vectors
                sdir1 = Vector(sensor[1].getStartPoint().getTurned(position.orientation), direction)
                sdir2 = Vector(sensor[1].getEndPoint().getTurned(position.orientation), direction)
                # border opposite direction vectors
                bdir1 = Vector(border.getStartPoint(), odirection)
                bdir2 = Vector(border.getEndPoint(), odirection)
                # collision ratios
                ratios = ( getVectorIntersectionRatio(sdir1, border),
                           getVectorIntersectionRatio(sdir2, border),
                           getVectorIntersectionRatio(bdir1, sensor[1]),
                           getVectorIntersectionRatio(bdir2, sensor[1]) )
                # find the closest one
                for ratio in ratios:
                    if ratio \
                    and 0 < ratio[0] < distance \
                    and 0 <= ratio[1] <= 1:
                        distance = ratio[0]
                        sensedby = sensor[0]

            if sensedby:
                # position where marvin will collide
                p = Point(position.point.x + direction.x * distance,
                          position.point.y + direction.y * distance)
                collisions.append((distance, sensedby, p))

        collisions.sort(cmp=__order)
        return collisions

    def merge(self, radius):

        print "=== merge ==="

        """ delete all borders in conflict with self.driven """
        for drive in self.driven:
            enum = Enumerator(self.borders)
            while enum.next():
                v = enum.current()
                distance = min(getVectorToPointDistance(drive, v.getStartPoint()),
                               getVectorToPointDistance(drive, v.getEndPoint()))
                if distance < radius:
                    enum.prev()
                    self.borders.remove(v)

        """ merge borders that could be one """
        enum = Enumerator(self.borders)
        while enum.next():
            v1 = enum.current()
            subenum = Enumerator(self.borders)
            while subenum.next():
                v2 = subenum.current()
                if v1 == v2: continue
                distance = min(getVectorToPointDistance(v1, v2.getStartPoint()),
                               getVectorToPointDistance(v1, v2.getEndPoint()))
                if distance <= MERGE_RANGE:
                    comp = v1.compareGetMaxMin(v2)
                    distance = min(getVectorToPointDistance(Vector(comp[0], endPoint=comp[1]), comp[2]),
                                   getVectorToPointDistance(Vector(comp[0], endPoint=comp[1]), comp[3]))
                    if distance <= MERGE_RANGE:
                        v1.merge(v2)
                        subenum.prev()
                        self.borders.remove(v2)



    def routeIsSet(self):
        return len(self.waypoints)

