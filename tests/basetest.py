# -*- coding: utf8 -*-
import unittest
import sys
from os import path
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))

from flask_profiler import measure
from flask_profiler import flask_profiler
from flask_profiler import storage

# CONF = {
#     "enabled": True,
#     "storage": {
#         "engine": "mongodb",
#         "DATABASE": "flask_profiler_test",
#         "COLLECTION": "profiler",
#         "MONGO_URL": "mongodb://localhost"
#     }
# }
CONF = {
    "enabled": True,
    "storage": {
        "engine": "sqlite"
    }
}


class BasetTest(unittest.TestCase):

    def setUp(cls):
        flask_profiler.collection.truncate()

    @classmethod
    def setUpClass(cls):

        flask_profiler.collection = storage.getCollection(CONF["storage"])
