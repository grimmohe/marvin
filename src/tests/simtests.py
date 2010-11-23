'''
Created on 16.11.2010

@author: christoph
'''
import unittest
from sim import Simulator


class TestSimulator(unittest.TestCase):

    def _prepare(self, point):
        point.append({"x": point[1]["x"] - point[0]["x"], "y": point[1]["y"] - point[0]["y"]})
        return point

    def _testCheckSensorStatus(self, sim, sensor):

        border = self._prepare([{"x": 0, "y": 0}, {"x": 0, "y": 100}])
        self.failIf(sim.checkSensorStatus(sensor, border) < 1.0)

        border = self._prepare([{"x": 0, "y": 100}, {"x": 75, "y": 100}])
        self.failIf(sim.checkSensorStatus(sensor, border) < 1.0)

        border = self._prepare([{"x": 75, "y": 100}, {"x": 75, "y": 75}])
        self.failIf(sim.checkSensorStatus(sensor, border) < 1.0)

        border = self._prepare([{"x": 75, "y": 75}, {"x": 100, "y": 75}])
        self.failIf(sim.checkSensorStatus(sensor, border) < 1.0)

        border = self._prepare([{"x": 100, "y": 75}, {"x": 100, "y": 0}])
        self.failIf(sim.checkSensorStatus(sensor, border) < 1.0)

        border = self._prepare([{"x": 100, "y": 0}, {"x": 0, "y": 0}])
        self.failIf(sim.checkSensorStatus(sensor, border) < 1.0)

        border = self._prepare([{"x": 100, "y": 0}, {"x": 0, "y": 0}])
        self.failIf(sim.checkSensorStatus(sensor, border) < 1.0)


    def testCheckSensorStatus(self):
        sim = Simulator(True)

        sensor = self._prepare([{"x": 48.74, "y": 78.85}, {"x": 19.28, "y": 51.80}])
        self._testCheckSensorStatus(sim, sensor)

        sensor = self._prepare([{"x": 21.01, "y": 51.32}, {"x": 6.61, "y": 65.20}])
        self._testCheckSensorStatus(sim, sensor)

        sensor = self._prepare([{"x": 1.0, "y": 51.32}, {"x": 1.0, "y": 65.20}])
        self._testCheckSensorStatus(sim, sensor)




if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testCheckSensorStatus']
    unittest.main()