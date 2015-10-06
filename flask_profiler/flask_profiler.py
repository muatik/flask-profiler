# -*- coding: utf8 -*-
from timeit import default_timer
import time
import functools
from flask import request, jsonify
import storage

collection = None


class Measurement(object):
    """represents an endpoint measurement"""
    DECIMAL_PLACES = 5

    def __init__(self, name, method, context=None):
        super(Measurement, self).__init__()
        self.context = context
        self.name = name
        self.method = method
        self.startedAt = 0
        self.endedAt = 0
        self.elapsed = 0

    def __json__(self):
        return {
            "name": self.name,
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


def wrap_to_measure(endpoint, f, method, context=None):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        measurement = Measurement(endpoint, method, context)
        measurement.start()

        try:
            returnVal = f(*args, **kwargs)
            time.sleep(1)
        except Exception, e:
            returnVal = None
        finally:
            measurement.stop()

        collection.insert(measurement.__json__())

        return returnVal

    return wrapper


def wrap_http_endpoint(endpoint, f, request=None):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        context = {
            "url": request.base_url,
            "args": dict(request.args.items()),
            "form": dict(request.form.items()),
            "body": request.data,
            "headers": dict(request.headers.items())}
        wrapped = wrap_to_measure(endpoint, f, request.method, context)
        return wrapped(*args, **kwargs)
    return wrapper


def wrapAppEndpoints(app):
    """
    wraps all endpoints defined in the given flask app to measure how long time
    each endpoints takes while being executed. This wrapping process is
    supposed not to change endpoint behaviour.
    """
    for endpoint, func in app.view_functions.iteritems():
        app.view_functions[endpoint] = wrap_http_endpoint(
            endpoint,
            func,
            request=request)


def registerInternalRouters(app):
    """
    These are the endponts which are used to display measurements in the
    flask-profiler dashboard.

    Note: these should be defined after wrapping user defined endpoints
    via wrapAppEndpoints()
    """

    @app.route("/flaskp/filter/")
    def filterMeasurements():
        args = dict(request.args.items())
        # r = {}
        # args = dict(request.args.items())
        # a = collection.find()
        # for i in a:
        #     i["_id"] = str(i["_id"])
        #     i["endedAt"] = str(i["endedAt"])
        #     i["startedAt"] = str(i["startedAt"])
        #     r[i["_id"]] = i
        # return jsonify(r)
        print args
        return jsonify(collection.filter(args))

    @app.route("/flaskp/summary/")
    def getMeasurementsSummary():
        args = dict(request.args.items())
        return jsonify(collection.getSummary(args))

    @app.route("/flaskp/measuremetns/<measurementId>/context")
    def getContext(measurementId):
        return jsonify(collection.getContext(measurementId))

    @app.route("/flaskp/measuremetns/<measurementId>/context")
    def getMeasurement(measurementId):
        return jsonify(collection.get(measurementId))


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
