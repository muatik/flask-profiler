# -*- coding: utf8 -*-
import unittest

from flask_testing import TestCase as FlaskTestCase

from .basetest import BasetTest, BaseTest2, flask_profiler


class EndpointMeasurementTest(BasetTest, FlaskTestCase):

    def tearDown(self):
        pass

    def test_01_return_value(self):
        name = "john"
        response = self.client.get("/api/people/{}".format(name))
        # converting because in python 3, reponse data becomes binary not utf-8
        r = response.data.decode("utf-8", "strict")
        self.assertEqual(r, name)

    def test_02_without_profiler(self):
        response = self.client.get("/api/without/profiler")
        # converting because in python 3, reponse data becomes binary not utf-8
        r = response.data.decode("utf-8", "strict")

        self.assertEqual(r, "without profiler")
        measurements = list(flask_profiler.collection.filter())
        self.assertEqual(len(measurements), 0)

    def test_02_with_profiler(self):
        response = self.client.get("/api/with/profiler/hello?q=1")
        # converting because in python 3, reponse data becomes binary not utf-8
        r = response.data.decode("utf-8", "strict")
        self.assertEqual(r, "with profiler")

        measurements = list(flask_profiler.collection.filter())
        self.assertEqual(len(measurements), 1)
        m = measurements[0]
        self.assertEqual(m["name"], "/api/with/profiler/<message>")
        self.assertEqual(m["method"], "GET")
        self.assertEqual(m["kwargs"], {"message": "hello"})
        self.assertEqual(m["context"]["args"], {"q": "1"})


class EndpointMeasurementTest2(BaseTest2, FlaskTestCase):

    def test_01_profiler(self):
        name = "foo"
        response = self.client.get("/api/people/{}".format(name))
        measurements = list(flask_profiler.collection.filter())
        self.assertEqual(len(measurements), 1)
        r = response.data.decode("utf-8", "strict")
        self.assertEqual(r, name)

    def test_02_profiler(self):
        self.client.get("/api/people/foo")
        self.client.get("/api/people/foo")
        self.client.get("/api/with/profiler/hello?q=2")
        measurements = list(flask_profiler.collection.filter({"sort": "id,desc"}))
        self.assertEqual(len(measurements), 3)
        m = measurements[0]
        self.assertEqual(m["name"], "/api/with/profiler/<message>")
        self.assertEqual(m["method"], "GET")
        self.assertEqual(m["kwargs"], {"message": "hello"})
        self.assertEqual(m["context"]["args"], {"q": "2"})


if __name__ == '__main__':
    unittest.main()
