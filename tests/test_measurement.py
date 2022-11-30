# -*- coding: utf-8 -*-
import time
import unittest

from flask_testing import TestCase

from flask_profiler.flask_profiler import Configuration, DependencyInjector, measure

from .basetest import BasetTest


def doWait(seconds, **kwargs):
    time.sleep(seconds)
    return seconds


class MeasurementTest(BasetTest, TestCase):
    def setUp(self) -> None:
        super().setUp()
        injector = DependencyInjector()
        self.controller = injector.get_filter_controller()

    def test_01_returnValue(self):
        wrapped = measure(doWait, "doWait", "call", context=None)
        waitSeconds = 1
        result = wrapped(waitSeconds)
        self.assertEqual(waitSeconds, result)

    def test_02_measurement(self):
        config = Configuration(self.app)
        wrapped = measure(doWait, "doWait", "call", context=None)
        waitSeconds = 2
        wrapped(waitSeconds)
        m = list(config.collection.filter(self.controller.parse_filter()))[0]
        self.assertEqual(m["name"], "doWait")
        self.assertEqual(float(m["elapsed"]) >= waitSeconds, True)

    def test_03_measurement_params(self):
        config = Configuration(self.app)
        context = {"token": "x"}
        name = "name_of_func"
        method = "invoke"
        wrapped = measure(doWait, name, method, context=context)

        waitSeconds = 1
        kwargs = {"k1": "kval1", "k2": "kval2"}
        wrapped(waitSeconds, **kwargs)
        m = list(config.collection.filter(self.controller.parse_filter()))[0]
        self.assertEqual(m["name"], name)
        self.assertEqual(m["method"], method)
        self.assertEqual(m["args"][0], waitSeconds)
        self.assertEqual(m["kwargs"], kwargs)
        self.assertEqual(m["context"], context)
        self.assertTrue(float(m["elapsed"]) >= waitSeconds)


if __name__ == "__main__":
    unittest.main()
