'''
Created on 10.08.2010

@author: christoph
'''
import unittest
import map
import mathix


class TestIntersections(unittest.TestCase):

    def testIntersectionBoth(self):
        vector1 = map.Vector(map.Point(0, 0), map.Point(5, 1))
        vector2 = map.Vector(map.Point(3, -1), map.Point(0, 3))
        ratio = mathix.getVectorIntersectionRatio(vector1, vector2)
        self.failUnless(0<=ratio[0]<=1, ratio)
        self.failUnless(0<=ratio[1]<=1, ratio)

    def testIntersectionNone(self):
        vector1 = map.Vector(map.Point(0, 0), map.Point(5, 1))
        vector2 = map.Vector(map.Point(6, 0), map.Point(1, 1))
        ratio = mathix.getVectorIntersectionRatio(vector1, vector2)
        self.failIf(0<=ratio[0]<=1, ratio)
        self.failIf(0<=ratio[1]<=1, ratio)

    def testIntersectionOn1(self):
        vector1 = map.Vector(map.Point(4, 4), map.Point(8, 1))
        vector2 = map.Vector(map.Point(9, 3), map.Point(1, 1))
        ratio = mathix.getVectorIntersectionRatio(vector1, vector2)
        self.failUnless(0<=ratio[0]<=1, ratio)
        self.failIf(0<=ratio[1]<=1, ratio)

    def testIntersectionOn2(self):
        vector1 = map.Vector(map.Point(4, 4), map.Point(5, 1))
        vector2 = map.Vector(map.Point(9, 3), map.Point(1, 7))
        ratio = mathix.getVectorIntersectionRatio(vector1, vector2)
        self.failIf(0<=ratio[0]<=1, ratio)
        self.failUnless(0<=ratio[1]<=1, ratio)

    def testIntersectionparallel(self):
        vector1 = map.Vector(map.Point(5, 5), map.Point(5, 1))
        vector2 = map.Vector(map.Point(6, 6), map.Point(5, 1))
        ratio = mathix.getVectorIntersectionRatio(vector1, vector2)
        self.failIf(ratio, ratio)

class TestAngleWithin(unittest.TestCase):

    def testWithinEasy(self):
        self.failUnless(mathix.angleWithin(20, 78, 45))

    def testWithinBorder(self):
        self.failUnless(mathix.angleWithin(350, 70, 355))

    def testWithinBorder2(self):
        self.failUnless(mathix.angleWithin(350, 70, 20))

    def testFailEasy(self):
        self.failIf(mathix.angleWithin(20, 70, 355))

    def testFailBorder(self):
        self.failIf(mathix.angleWithin(320, 70, 300))

    def testFailBorder2(self):
        self.failIf(mathix.angleWithin(320, 70, 80))

if __name__ == "__main__":
    unittest.main()