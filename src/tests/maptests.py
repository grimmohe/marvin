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


if __name__ == "__main__":
    unittest.main()