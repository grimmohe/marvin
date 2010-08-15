'''
Created on 10.08.2010

@author: christoph
'''
import unittest
import map


class TestAreaIntersections(unittest.TestCase):

    def testIntersectionFull(self):
        area = map.Area(map.Point(0, 0), map.Point(5, 0), map.Point(0, 5))
        vector = map.Vector(map.Point(1, -3), map.Point(1, 10))
        self.failUnless(area.intersects(vector))

    def testIntersectionHalf_1213(self):
        area = map.Area(map.Point(0, 0), map.Point(5, 0), map.Point(0, 5))
        vector = map.Vector(map.Point(3, -1), map.Point(-2, 2))
        self.failUnless(area.intersects(vector))

    def testIntersectionHalf_1223(self):
        area = map.Area(map.Point(0, 0), map.Point(5, 0), map.Point(0, 5))
        vector = map.Vector(map.Point(3, -1), map.Point(0, 2))
        self.failUnless(area.intersects(vector))

    def testIntersectionHalf_1323(self):
        area = map.Area(map.Point(0, 0), map.Point(5, 0), map.Point(0, 5))
        vector = map.Vector(map.Point(-2, 2), map.Point(3, 1))
        self.failUnless(area.intersects(vector))

    def testIntersectionWithin_1213(self):
        area = map.Area(map.Point(0, 0), map.Point(5, 0), map.Point(0, 5))
        vector = map.Vector(map.Point(1, 2), map.Point(1, -1))
        self.failUnless(area.intersects(vector))

    def testIntersectionWithin_1223(self):
        area = map.Area(map.Point(0, 0), map.Point(5, 0), map.Point(0, 5))
        vector = map.Vector(map.Point(2, 1), map.Point(1, 1))
        self.failUnless(area.intersects(vector))

    def testIntersectionWithin_1323(self):
        area = map.Area(map.Point(0, 0), map.Point(5, 0), map.Point(0, 5))
        vector = map.Vector(map.Point(1, 2), map.Point(1, 1))
        self.failUnless(area.intersects(vector))

    def testIntersectionWithin_HitAll(self):
        area = map.Area(map.Point(0, 0), map.Point(5, 0), map.Point(0, 5))
        vector = map.Vector(map.Point(1, 1), map.Point(1, 1))
        self.failUnless(area.intersects(vector))

    def testIntersectionNone(self):
        area = map.Area(map.Point(0, 0), map.Point(5, 0), map.Point(0, 5))
        vector = map.Vector(map.Point(1, -3), map.Point(7, -1))
        self.failIf(area.intersects(vector))

class TestVectorCopy(unittest.TestCase):

    def testCopyNone(self):
        vector = map.Vector(map.Point(1, 2), map.Point(3, 4))
        copy = vector.copy()
        self.failUnless(vector.point.x == copy.point.x)
        self.failUnless(vector.point.y == copy.point.y)
        self.failUnless(vector.size.x == copy.size.x)
        self.failUnless(vector.size.y == copy.size.y)

    def testCopyMove(self):
        vector = map.Vector(map.Point(1, 2), map.Point(3, 4))
        copy = vector.copy(map.Point(5, 2))
        self.failUnless(copy.point.x == 6)
        self.failUnless(copy.point.y == 4)
        self.failUnless(copy.size.x == vector.size.x)
        self.failUnless(copy.size.y == vector.size.y)

    def testCopyMoveTurn(self):
        vector = map.Vector(map.Point(1, 2), map.Point(3, 4))
        copy = vector.copy(map.Point(5, 2), 90)
        self.failUnless(copy.point.x == 7)
        self.failUnless(copy.point.y == 1)
        self.failUnless(copy.size.x == 4)
        self.failUnless(copy.size.y == -3)

    def testCopyOffset(self):
        vector = map.Vector(map.Point(1, 2), map.Point(3, 0))
        copy = vector.copy(offset=map.Vector(map.Point(0, 0), map.Point(0, 1)))
        self.failUnless(copy.point.x == 1)
        self.failUnless(copy.point.y == 3)
        self.failUnless(copy.size.x == vector.size.x)
        self.failUnless(copy.size.y == vector.size.y)

    def testCopyAll(self):
        vector = map.Vector(map.Point(1, 2), map.Point(4, 4))
        copy = vector.copy(map.Point(5, 2), 90, map.Vector(map.Point(0, 0), map.Point(1, -1)))
        self.failUnless(copy.point.x == 6)
        self.failUnless(copy.point.y == 0)
        self.failUnless(copy.size.x == 4)
        self.failUnless(copy.size.y == -4)


if __name__ == "__main__":
    unittest.main()