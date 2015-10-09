# -*- coding: utf8 -*-
from timeit import default_timer
import time
import functools
from flask import request, jsonify
import storage
from pprint import pprint as pp

collection = None


class Measurement(object):
    """represents an endpoint measurement"""
    DECIMAL_PLACES = 6

    def __init__(self, name, args, kwargs, method, context=None):
        super(Measurement, self).__init__()
        self.context = context
        self.name = name
        self.method = method
        self.args = args
        self.kwargs = kwargs
        self.startedAt = 0
        self.endedAt = 0
        self.elapsed = 0

    def __json__(self):
        return {
            "name": self.name,
            "args": self.args,
            "kwargs": self.kwargs,
            "method": self.method,
            "startedAt": self.startedAt,
            "endedAt": self.endedAt,
            "elapsed": self.elapsed,
            "context": self.context
        }

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


def measure(f, name, method, context=None):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        if not collection:
            raise Exception(
                "before measuring anything, you need to call init_app()")

        measurement = Measurement(name, args, kwargs, method, context)
        measurement.start()

        try:
            returnVal = f(*args, **kwargs)
        except Exception, e:
            raise e
        finally:
            measurement.stop()
            pp(measurement.__json__())
            collection.insert(measurement.__json__())

        return returnVal

    return wrapper


def wrapHttpEndpoint(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        context = {
            "url": request.base_url,
            "args": dict(request.args.items()),
            "form": dict(request.form.items()),
            "body": request.data,
            "headers": dict(request.headers.items()),
            "func": request.endpoint}
        endpoint_name = str(request.url_rule)
        wrapped = measure(f, endpoint_name, request.method, context)
        return wrapped(*args, **kwargs)
    return wrapper


def wrapAppEndpoints(app):
    """
    wraps all endpoints defined in the given flask app to measure how long time
    each endpoints takes while being executed. This wrapping process is
    supposed not to change endpoint behaviour.
    """
    for endpoint, func in app.view_functions.iteritems():
        app.view_functions[endpoint] = wrapHttpEndpoint(func)


def profile(*args, **kwargs):
    """
    http endpoint decorator
    """
    def wrapper(f):
        return wrapHttpEndpoint(f)
    return wrapper


def registerInternalRouters(app):
    """
    These are the endponts which are used to display measurements in the
    flask-profiler dashboard.

    Note: these should be defined after wrapping user defined endpoints
    via wrapAppEndpoints()
    """

    urlPath = CONF.get("urlPath", "flask-profiler")

    @app.route("/{}/measurements/".format(urlPath))
    def filtermeasurements():
        args = dict(request.args.items())
        measurements = collection.filter(args)
        return jsonify({"measurements": list(measurements)})

    @app.route("/{}/measurements/grouped/".format(urlPath))
    def getmeasurementsSummary():
        args = dict(request.args.items())
        print args
        measurements = collection.getSummary(args)
        return jsonify({"measurements": list(measurements)})

    @app.route("/{}/measurements/<measurementId>".format(urlPath))
    def getContext(measurementId):
        return jsonify(collection.getContext(measurementId))


def init_app(app):
    global collection, CONF

    try:
        CONF = app.config["flask_profiler"]
    except Exception, e:
        raise Exception(
            "to init flask-profiler, provide "
            "required config through flask app's config. please refer: "
            "@TODO: link here")

    collection = storage.getCollection(CONF.get("storage", {}))
    wrapAppEndpoints(app)
    registerInternalRouters(app)
