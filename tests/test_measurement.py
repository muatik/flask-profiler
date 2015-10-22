# -*- coding: utf8 -*-
import unittest
from .basetest import BasetTest, measure, flask_profiler
import time
from pprint import pprint as pp


def doWait(seconds, **kwargs):
    time.sleep(seconds)
    return seconds


class MeasurementTest(BasetTest):

    def setUp(self):
        flask_profiler.collection.truncate()

    def test_01_returnValue(self):
        wrapped = measure(doWait, "doWait", "call", context=None)
        waitSeconds = 1
        result = wrapped(waitSeconds)
        self.assertEqual(waitSeconds, result)

    def test_02_measurement(self):
        wrapped = measure(doWait, "doWait", "call", context=None)
        waitSeconds = 2
        result = wrapped(waitSeconds)
        m = list(flask_profiler.collection.filter())[0]
        self.assertEqual(m["name"], "doWait")
        self.assertTrue(float(m["elapsed"]) >= waitSeconds)

    def test_03_measurement_params(self):
        context = {"token": "x"}
        name = "name_of_func"
        method = "invoke"
        wrapped = measure(doWait, name, method, context=context)

        waitSeconds = 1
        kwargs = {"k1": "kval1", "k2": "kval2"}
        result = wrapped(waitSeconds, **kwargs)
        m = list(flask_profiler.collection.filter())[0]
        self.assertEqual(m["name"], name)
        self.assertEqual(m["method"], method)
        self.assertEqual(m["args"][0], waitSeconds)
        self.assertEqual(m["kwargs"], kwargs)
        self.assertEqual(m["context"], context)
        self.assertTrue(float(m["elapsed"]) >= waitSeconds)

if __name__ == '__main__':
    unittest.main()
