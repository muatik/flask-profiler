# -*- coding: utf8 -*-
import unittest
import sys
from os import environ, path
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))

from flask_profiler import measure
from flask_profiler import flask_profiler
from flask_profiler import storage

_CONFS = {
    "mongodb": {
        "enabled": True,
        "storage": {
            "engine": "mongodb",
            "DATABASE": "flask_profiler_test",
            "COLLECTION": "profiler",
            "MONGO_URL": "mongodb://localhost"
        }
    },
    "sqlite": {
        "enabled": True,
        "storage": {
            "engine": "sqlite"
        }
    }
}
CONF = _CONFS[environ.get('FLASK_PROFILER_TEST_CONF', 'sqlite')]


class BasetTest(unittest.TestCase):

    def setUp(cls):
        flask_profiler.collection.truncate()

    @classmethod
    def setUpClass(cls):

        flask_profiler.collection = storage.getCollection(CONF["storage"])
