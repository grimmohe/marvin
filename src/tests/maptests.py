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

    def testVectorCopyEqual(self):
        vector = map.Vector(map.Point(0, 2), map.Point(1, 0))
        copy = vector.copy()
        self.failUnless(vector.point.x == copy.point.x
                        and vector.point.y == copy.point.y
                        and vector.size.x == copy.size.x
                        and vector.size.y == copy.size.y, copy)

    def testVectorCopyMoved(self):
        vector = map.Vector(map.Point(0, 2), map.Point(1, 0))
        copy = vector.copy(map.Point(1, 1))
        self.failUnless(copy.point.x == 1
                        and copy.point.y == 3
                        and copy.size.x == vector.size.x
                        and copy.size.y == vector.size.y, copy)

    def testVectorCopyTurned(self):
        vector = map.Vector(map.Point(0, 2), map.Point(1, 0))
        copy = vector.copy(map.Point(0, 0), 90)
        self.failUnless(copy.point.x == 2
                        and copy.point.y == 0
                        and copy.size.x == 0
                        and copy.size.y == -1, copy)

    def testVectorCopyMovedAndTurned(self):
        vector = map.Vector(map.Point(0, 2), map.Point(1, 0))
        copy = vector.copy(map.Point(1, 1), 90)
        self.failUnless(copy.point.x == 3
                        and copy.point.y == 1
                        and copy.size.x == 0
                        and copy.size.y == -1, copy)


class TestVectorCombine(unittest.TestCase):

    def testVectorCombine(self):
        vector1 = map.Vector(map.Point(0, 0), map.Point(5, 1))
        vector2 = map.Vector(map.Point(0, 2), map.Point(5, 0))
        combination = map.Vector().combine(vector1, vector2, map.Vector.START_POINT)
        self.failUnless(combination.point.x == 0
                        and combination.point.y == 0
                        and combination.size.x == 0
                        and combination.size.y == 2, combination)

        combination = map.Vector().combine(vector1, vector2, map.Vector.END_POINT)
        self.failUnless(combination.point.x == 5
                        and combination.point.y == 1
                        and combination.size.x == 0
                        and combination.size.y == 1, combination)


if __name__ == "__main__":
    unittest.main()