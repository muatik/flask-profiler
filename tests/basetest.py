# -*- coding: utf-8 -*-
import unittest
from copy import copy

from flask import Flask

from flask_profiler import flask_profiler
from flask_profiler.flask_profiler import Configuration

CONF = {
    "enabled": True,
    "storage": {"engine": "sqlite", "file": ":memory:"},
    "ignore": ["^/static/.*"],
}


class BasetTest(unittest.TestCase):
    app: Flask

    def tearDown(self) -> None:
        config = Configuration(self.app)
        config.collection.truncate()
        super().tearDown()

    def override_config(self, config):
        return config

    def create_app(self):
        app = Flask(__name__)
        app.config["flask_profiler"] = self.override_config(copy(CONF))
        app.config["TESTING"] = True

        @app.route("/api/people/<firstname>")
        def sayHello(firstname):
            return firstname

        @app.route("/static/photo/")
        def getStaticPhoto():
            return "your static photo"

        @app.route("/static/")
        def getStatic():
            return "your static"

        @app.route("/api/static/")
        def getApiStatic():
            return "your api static"

        @app.route("/api/settings/system/secret/")
        def getSystemSettingsSecret():
            return "your system settings secret"

        @app.route("/api/settings/personal/secret/")
        def getPersonalSettingsSecret():
            return "your personal settings secret"

        @app.route("/api/settings/personal/name/")
        def getPersonalSettingsName():
            return "your personal settings name"

        flask_profiler.init_app(app)

        @app.route("/api/without/profiler")
        def withoutProfiler():
            return "without profiler"

        @app.route("/api/with/profiler/<message>")
        @flask_profiler.profile()
        def customProfilerEP(message):
            return "with profiler"

        return app


class BaseTest2(unittest.TestCase):
    app: Flask

    def tearDown(self) -> None:
        config = Configuration(self.app)
        config.collection.truncate()
        super().tearDown()

    def create_app(self):
        app = Flask(__name__)
        app.config["flask_profiler"] = CONF
        app.config["TESTING"] = True

        @app.route("/api/people/<firstname>")
        def sayHello(firstname):
            return firstname

        @app.route("/api/people/by-id/<uuid:id>")
        def helloUuidRoute(id):
            return str(id)

        @app.route("/api/with/profiler/<message>")
        def customProfilerEP(message):
            return "with profiler"

        flask_profiler.init_app(app)
        return app
