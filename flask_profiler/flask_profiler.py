# -*- coding: utf8 -*-
from timeit import default_timer
import time
import functools
from flask import request
from pymongo import MongoClient

storage = MongoClient()


class Measurement(object):
    """represents an endpoint measurement"""
    def __init__(self, request, endpoint, view_function):
        super(Measurement, self).__init__()
        self.request = request
        self.endpoint = endpoint
        self.view_function = view_function
        self.startedAt = 0
        self.endedAt = 0
        self.elapsed = 0

    def __json__(self):
        return {
            "request": {
                "url": self.request.base_url,
                "method": self.request.method,
                "args": dict(self.request.args.items()),
                "form": dict(self.request.form.items()),
                "body": self.request.data,
                "headers": dict(self.request.headers.items())},
            "endpoint": self.endpoint,
            "startedAt": self.startedAt,
            "endedAt": self.endedAt,
            "elapsed": self.elapsed
        }

    def __str__(self):
        return str(self.__json__())

    def start(self):
        # we use default_timer to get the best clock available.
        # see: http://stackoverflow.com/a/25823885/672798
        self.startedAt = default_timer()

    def stop(self):
        self.endedAt = default_timer()
        self.elapsed = self.endedAt - self.startedAt


def wrap_to_measure(endpoint, f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        measurement = Measurement(request, endpoint, f)
        measurement.start()

        try:
            returnVal = f(*args, **kwargs)
        except Exception, e:
            returnVal = None
        finally:
            measurement.start()

        storage.insert(measurement)

        return returnVal

    return wrapper


def init_app(app):
    for endpoint, func in app.view_functions.iteritems():
        app.view_functions[endpoint] = wrap_to_measure(endpoint, func)
