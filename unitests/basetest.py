# -*- coding: utf8 -*-
import unittest
import sys
from os import path
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))

from flask_profiler import measure
from flask_profiler import flask_profiler
from flask_profiler import storage

CONF = {
    "engine": "mongodb",
    "database": "flask_profiler_test",
    "collection": "profiler",
    "mongo_url": ""
}


class BasetTest(unittest.TestCase):

    def setUp(cls):
        flask_profiler.collection.remove()

    @classmethod
    def setUpClass(cls):

        flask_profiler.collection = storage.getCollection(CONF)
