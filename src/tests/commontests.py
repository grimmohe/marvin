'''
Created on 27.08.2010

@author: christoph
'''
import unittest
from common import SortedList
from map import Vector


class TestSortedList(unittest.TestCase):

    def _compare(self, v1, v2):
        return id(v1) - id(v2)

    def test1(self):
        list = SortedList(self._compare)
        list.append(Vector())
        v = Vector()
        list.append(v)
        list.append(Vector())
        list.append(Vector())
        self.failUnless(v == list.pop(list.find(v)))

if __name__ == "__main__":
    unittest.main()