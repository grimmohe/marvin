'''
Created on 10.08.2010

@author: christoph
'''
import unittest
from map import Area, Map, Point, Position, Vector


class TestAreaIntersections(unittest.TestCase):

    def testIntersectionFull(self):
        area = Area(Point(0, 0), Point(5, 0), Point(0, 5))
        vector = Vector(Point(1, -3), Point(1, 10))
        self.failUnless(area.intersects(vector))

    def testIntersectionHalf_1213(self):
        area = Area(Point(0, 0), Point(5, 0), Point(0, 5))
        vector = Vector(Point(3, -1), Point(-2, 2))
        self.failUnless(area.intersects(vector))

    def testIntersectionHalf_1223(self):
        area = Area(Point(0, 0), Point(5, 0), Point(0, 5))
        vector = Vector(Point(3, -1), Point(0, 2))
        self.failUnless(area.intersects(vector))

    def testIntersectionHalf_1323(self):
        area = Area(Point(0, 0), Point(5, 0), Point(0, 5))
        vector = Vector(Point(-2, 2), Point(3, 1))
        self.failUnless(area.intersects(vector))

    def testIntersectionWithin_1213(self):
        area = Area(Point(0, 0), Point(5, 0), Point(0, 5))
        vector = Vector(Point(1, 2), Point(1, -1))
        self.failUnless(area.intersects(vector))

    def testIntersectionWithin_1223(self):
        area = Area(Point(0, 0), Point(5, 0), Point(0, 5))
        vector = Vector(Point(2, 1), Point(1, 1))
        self.failUnless(area.intersects(vector))

    def testIntersectionWithin_1323(self):
        area = Area(Point(0, 0), Point(5, 0), Point(0, 5))
        vector = Vector(Point(1, 2), Point(1, 1))
        self.failUnless(area.intersects(vector))

    def testIntersectionWithin_HitAll(self):
        area = Area(Point(0, 0), Point(5, 0), Point(0, 5))
        vector = Vector(Point(1, 1), Point(1, 1))
        self.failUnless(area.intersects(vector))

    def testIntersectionNone(self):
        area = Area(Point(0, 0), Point(5, 0), Point(0, 5))
        vector = Vector(Point(1, -3), Point(7, -1))
        self.failIf(area.intersects(vector))

class TestMapNextCollisionIn(unittest.TestCase):

    def testNextCollisionInNone(self):
        map = Map()
        map.addBorder(Vector(Point(0, 50), Point(10, 0)))
        map.addBorder(Vector(Point(50, 0), Point(0, 10)))
        sensors = [Vector(Point(-5, 5), Point(10, 0))]
        collision = map.nextCollisionIn(Position(Point(0, 0), 45), sensors)
        self.failIf(collision[1], "collision where none expected")

    def testNextCollisionInNr1(self):
        map = Map()
        map.addBorder(Vector(Point(0, 50), Point(10, 0)))
        map.addBorder(Vector(Point(50, 0), Point(0, 10)))
        sensors = [Vector(Point(-5, 5), Point(10, 0))]
        collision = map.nextCollisionIn(Position(Point(0, 0), 0), sensors)
        self.failUnless(collision[1] == sensors[0])
        self.failUnless(collision[0] == 45)

    def testNextCollisionInNr2(self):
        map = Map()
        map.addBorder(Vector(Point(0, 50), Point(4, 0)))
        map.addBorder(Vector(Point(50, 0), Point(0, 10)))
        sensors = [Vector(Point(-5, 5), Point(10, 0))]
        collision = map.nextCollisionIn(Position(Point(0, 0), 0), sensors)
        self.failUnless(collision[1] == sensors[0])
        self.failUnless(collision[0] == 45)

class TestMapGetLooseEnds(unittest.TestCase):

    def testGetLooseEndsNone(self):
        map = Map()
        map.addBorder(Vector(Point(0, 0), Point(10, 0)))
        map.addBorder(Vector(Point(10, 0.9), Point(0, 10)))
        map.addBorder(Vector(Point(10, 10), Point(-10, 0)))
        map.addBorder(Vector(Point(0, 10), Point(0, -10)))
        loose = map.getLooseEnds()
        self.failUnless(len(loose) == 0, len(loose))

    def testGetLooseEnds2(self):
        map = Map()
        map.addBorder(Vector(Point(0, 0), Point(10, 0)))
        map.addBorder(Vector(Point(10, 0.9), Point(0, 10)))
        map.addBorder(Vector(Point(10, 10), Point(-10, 0)))
        loose = map.getLooseEnds()
        self.failUnless(len(loose) == 2, len(loose))
        self.failUnless(loose[0].point.x == 10
                        and loose[0].point.y == 0
                        and loose[0].size.x == -10
                        and loose[0].size.y == 0)
        self.failUnless(loose[1].point.x == 10
                        and loose[1].point.y == 10
                        and loose[1].size.x == -10
                        and loose[1].size.y == 0)

class TestVectorCopy(unittest.TestCase):

    def testCopyNone(self):
        vector = Vector(Point(1, 2), Point(3, 4))
        copy = vector.copy()
        self.failUnless(vector.point.x == copy.point.x)
        self.failUnless(vector.point.y == copy.point.y)
        self.failUnless(vector.size.x == copy.size.x)
        self.failUnless(vector.size.y == copy.size.y)

    def testCopyMove(self):
        vector = Vector(Point(1, 2), Point(3, 4))
        copy = vector.copy(Point(5, 2))
        self.failUnless(copy.point.x == 6)
        self.failUnless(copy.point.y == 4)
        self.failUnless(copy.size.x == vector.size.x)
        self.failUnless(copy.size.y == vector.size.y)

    def testCopyMoveTurn(self):
        vector = Vector(Point(1, 2), Point(3, 4))
        copy = vector.copy(Point(5, 2), 90)
        self.failUnless(copy.point.x == 7)
        self.failUnless(copy.point.y == 1)
        self.failUnless(copy.size.x == 4)
        self.failUnless(copy.size.y == -3)

    def testCopyOffset(self):
        vector = Vector(Point(1, 2), Point(3, 0))
        copy = vector.copy(offset=Vector(Point(0, 0), Point(0, 1)))
        self.failUnless(copy.point.x == 1)
        self.failUnless(copy.point.y == 3)
        self.failUnless(copy.size.x == vector.size.x)
        self.failUnless(copy.size.y == vector.size.y)

    def testCopyAll(self):
        vector = Vector(Point(1, 2), Point(4, 4))
        copy = vector.copy(Point(5, 2), 90, Vector(Point(0, 0), Point(1, -1)))
        self.failUnless(copy.point.x == 6)
        self.failUnless(copy.point.y == 0)
        self.failUnless(copy.size.x == 4)
        self.failUnless(copy.size.y == -4)


class TestVectorCombine(unittest.TestCase):

    def testCombine(self):
        vector1 = Vector(Point(0, 0), Point(5, 1))
        vector2 = Vector(Point(0, 2), Point(5, 0))
        combination = Vector().combine(vector1, vector2, Vector.START_POINT)
        self.failUnless(combination.point.x == 0
                        and combination.point.y == 0
                        and combination.size.x == 0
                        and combination.size.y == 2, combination)

        combination = Vector().combine(vector1, vector2, Vector.END_POINT)
        self.failUnless(combination.point.x == 5
                        and combination.point.y == 1
                        and combination.size.x == 0
                        and combination.size.y == 1, combination)

class TestVectorIsConnected(unittest.TestCase):

    def testIsConnectedNone(self):
        vector1 = Vector(Point(0, 0), Point(10, 0))
        vector2 = Vector(Point(2, 2), Point(10, 0))
        self.failIf(vector1.isConnected(vector2))

    def testIsConnectedEnd(self):
        vector1 = Vector(Point(0, 0), Point(10, 0))
        vector2 = Vector(Point(0.5, 0.5), Point(10, 10))
        self.failUnless(vector1.isConnected(vector2))

    def testIsConnectedBetween(self):
        vector1 = Vector(Point(0, 0), Point(10, 0))
        vector2 = Vector(Point(4, 0.5), Point(10, 10))
        self.failUnless(vector1.isConnected(vector2))


if __name__ == "__main__":
    unittest.main()