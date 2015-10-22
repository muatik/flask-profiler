# -*- coding: utf8 -*-
import unittest
from .basetest import BasetTest, measure, flask_profiler, CONF
import time
from pprint import pprint as pp
from flask import Flask
from flask.ext.testing import TestCase as FlaskTestCase


class EndpointMeasurementTest(BasetTest, FlaskTestCase):

    def create_app(self):
        app = Flask(__name__)
        app.config["flask_profiler"] = CONF
        app.config['TESTING'] = True

        @app.route("/api/people/<firstname>")
        def sayHello(firstname):
            return firstname

        flask_profiler.init_app(app)

        @app.route("/api/without/profiler")
        def withoutProfiler():
            return "without profiler"

        @app.route("/api/with/profiler/<message>")
        @flask_profiler.profile()
        def customProfilerEP(message):
            return "with profiler"

        return app

    def tearDown(self):
        pass

    def test_01_return_value(self):
        name = "john"
        response = self.client.get("/api/people/{}".format(name))
        # converting because in python 3, reponse data becomes binary not utf-8
        r = response.data.decode("utf-8", "strict")
        self.assertEquals(r, name)

    def test_02_without_profiler(self):
        response = self.client.get("/api/without/profiler")
        # converting because in python 3, reponse data becomes binary not utf-8
        r = response.data.decode("utf-8", "strict")

        self.assertEquals(r, "without profiler")
        measurements = list(flask_profiler.collection.filter())
        self.assertEquals(len(measurements), 0)

    def test_02_with_profiler(self):
        response = self.client.get("/api/with/profiler/hello?q=1")
        # converting because in python 3, reponse data becomes binary not utf-8
        r = response.data.decode("utf-8", "strict")
        self.assertEquals(r, "with profiler")

        measurements = list(flask_profiler.collection.filter())
        self.assertEquals(len(measurements), 1)
        m = measurements[0]
        self.assertEqual(m["name"], "/api/with/profiler/<message>")
        self.assertEqual(m["method"], "GET")
        self.assertEqual(m["kwargs"], {"message": "hello"})
        self.assertEqual(m["context"]["args"], {"q": "1"})

if __name__ == '__main__':
    unittest.main()
