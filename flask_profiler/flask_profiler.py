# -*- coding: utf8 -*-
from timeit import default_timer
import time
import functools
from flask import request
from pymongo import MongoClient

storage = MongoClient()["profiler"]["measurements"]


class Measurement(object):
    """represents an endpoint measurement"""
    DECIMAL_PLACES = 5

    def __init__(self, name, request=None):
        super(Measurement, self).__init__()
        self.request = request
        self.name = name
        self.startedAt = 0
        self.endedAt = 0
        self.elapsed = 0

    def __json__(self):
        data = {
            "name": self.name,
            "startedAt": self.startedAt,
            "endedAt": self.endedAt,
            "elapsed": self.elapsed
        }

        if self.request:
            data["request"] = {
                "url": self.request.base_url,
                "method": self.request.method,
                "args": dict(self.request.args.items()),
                "form": dict(self.request.form.items()),
                "body": self.request.data,
                "headers": dict(self.request.headers.items())}

        return data

    def __str__(self):
        return str(self.__json__())

    def start(self):
        # we use default_timer to get the best clock available.
        # see: http://stackoverflow.com/a/25823885/672798
        self.startedAt = default_timer()

    def stop(self):
        self.endedAt = default_timer()
        self.elapsed = round(
            self.endedAt - self.startedAt, self.DECIMAL_PLACES)


def getMeasurements():
    return storage.find(
        keyword=None,
        sortBy="startedAt",
        endTime=None,
        startTime=None,
        elapsedMoreThan=0
        )


def wrap_to_measure(endpoint, f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        measurement = Measurement(endpoint)
        measurement.start()

        try:
            returnVal = f(*args, **kwargs)
            time.sleep(1)
        except Exception, e:
            returnVal = None
        finally:
            measurement.stop()

        storage.insert(measurement.__json__())

        return returnVal

    return wrapper


def init_app(app):
    for endpoint, func in app.view_functions.iteritems():
        app.view_functions[endpoint] = wrap_to_measure(endpoint, func)
