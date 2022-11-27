# -*- coding: utf-8 -*-

import functools
import logging
import re
import time
from pprint import pprint as pp
from typing import List, Optional
from uuid import UUID

from flask import Blueprint, Flask, current_app, g, has_app_context, jsonify, request
from flask_httpauth import HTTPBasicAuth

from .storage.base import BaseStorage

logger = logging.getLogger("flask-profiler")


class Configuration:
    def __init__(self, app: Flask) -> None:
        self.app = app

    @property
    def enabled(self) -> bool:
        return read_config(self.app).get("enabled", False)

    def sampling_function(self) -> bool:
        config = read_config(self.app)
        if "sampling_function" not in config:
            return True
        elif not callable(config["sampling_function"]):
            raise Exception(
                "if sampling_function is provided to flask-profiler via config, "
                "it must be callable, refer to: "
                "https://github.com/muatik/flask-profiler#sampling"
            )
        else:
            return config["sampling_function"]()

    @property
    def ignore_patterns(self) -> List[str]:
        return read_config(self.app).get("ignore", [])

    @property
    def verbose(self) -> bool:
        return read_config(self.app).get("verbose", False)

    @property
    def url_prefix(self) -> str:
        return read_config(self.app).get("endpointRoot", "flask-profiler")

    @property
    def is_basic_auth_enabled(self) -> bool:
        return read_config(self.app).get("basicAuth", {}).get("enabled", False)

    @property
    def basic_auth_username(self) -> str:
        return read_config(self.app)["basicAuth"]["username"]

    @property
    def basic_auth_password(self) -> str:
        return read_config(self.app)["basicAuth"]["passwordb"]

    @property
    def collection(self) -> BaseStorage:
        if not has_app_context():
            return None
        collection = g.get("flask_profiler_collection")
        if collection is None:
            collection = self._create_storage()
            g.flask_profiler_collection = collection
        return collection

    def _create_storage(self) -> BaseStorage:
        conf = read_config(self.app).get("storage", {})
        engine = conf.get("engine", "")
        if engine.lower() == "mongodb":
            from .storage.mongo import Mongo

            return Mongo(
                mongo_url=conf.get("MONGO_URL", "mongodb://localhost"),
                database_name=conf.get("DATABASE", "flask_profiler"),
                collection_name=conf.get("COLLECTION", "measurements"),
            )
        elif engine.lower() == "sqlite":
            from .storage.sqlite import Sqlite

            return Sqlite(
                sqlite_file=conf.get("FILE", "flask_profiler.sql"),
                table_name=conf.get("TABLE", "measurements"),
            )
        elif engine.lower() == "sqlalchemy":
            from .storage.sql_alchemy import Sqlalchemy

            db_url = conf.get("db_url", "sqlite:///flask_profiler.sql")
            return Sqlalchemy(db_url=db_url)
        else:
            raise ValueError(
                (
                    "flask-profiler requires a valid storage engine but it is"
                    " missing or wrong. provided engine: {}".format(engine)
                )
            )


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
            "context": self.context,
        }

    def __str__(self):
        return str(self.__json__())

    def start(self):
        # we use default_timer to get the best clock available.
        # see: http://stackoverflow.com/a/25823885/672798
        self.startedAt = time.time()

    def stop(self):
        self.endedAt = time.time()
        self.elapsed = round(self.endedAt - self.startedAt, self.DECIMAL_PLACES)


def is_ignored(name: str) -> bool:
    config = Configuration(current_app)
    for pattern in config.ignore_patterns:
        if re.search(pattern, name):
            return True
    return False


def measure(f, name: str, method, context=None):
    logger.debug("{0} is being processed.")
    config = Configuration(current_app)
    if is_ignored(name):
        logger.debug("{0} is ignored.")
        return f

    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        if not config.sampling_function():
            return f(*args, **kwargs)

        measurement = Measurement(name, args, sanatize_kwargs(kwargs), method, context)
        measurement.start()

        try:
            returnVal = f(*args, **kwargs)
        finally:
            measurement.stop()
            if config.verbose:
                pp(measurement.__json__())
            config.collection.insert(measurement.__json__())

        return returnVal

    return wrapper


def wrapHttpEndpoint(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        context = {
            "url": request.base_url,
            "args": dict(request.args.items()),
            "form": dict(request.form.items()),
            "body": request.data.decode("utf-8", "strict"),
            "headers": dict(request.headers.items()),
            "func": request.endpoint,
            "ip": request.remote_addr,
        }
        endpoint_name = str(request.url_rule)
        wrapped = measure(f, endpoint_name, request.method, context)
        return wrapped(*args, **kwargs)

    return wrapper


def wrapAppEndpoints(app):
    """
    wraps all endpoints defined in the given flask app to measure how long time
    each endpoints takes while being executed. This wrapping process is
    supposed not to change endpoint behaviour.
    :param app: Flask application instance
    :return:
    """
    for endpoint, func in app.view_functions.items():
        app.view_functions[endpoint] = wrapHttpEndpoint(func)


def profile(*args, **kwargs):
    """
    http endpoint decorator
    """

    def wrapper(f):
        return wrapHttpEndpoint(f)

    return wrapper


def register_internal_routes(app: Flask, url_prefix: str = None) -> None:
    """
    These are the endpoints which are used to display measurements in the
    flask-profiler dashboard.

    Note: these should be defined after wrapping user defined endpoints
    via wrapAppEndpoints()
    :param app: Flask application instance
    :return:
    """
    config = Configuration(app)
    fp = Blueprint(
        "flask-profiler",
        __name__,
        url_prefix=f"/{config.url_prefix}",
        static_folder="static/dist/",
        static_url_path="/static/dist",
    )

    auth = HTTPBasicAuth()

    @auth.verify_password
    def verify_password(username, password):
        if not config.is_basic_auth_enabled:
            return True

        if (
            username == config.basic_auth_username
            and password == config.basic_auth_password
        ):
            return True
        logging.warning("flask-profiler authentication failed")
        return False

    @fp.route("/")
    @auth.login_required
    def index():
        return fp.send_static_file("index.html")

    @fp.route("/api/measurements/")
    @auth.login_required
    def filterMeasurements():
        args = dict(request.args.items())
        measurements = config.collection.filter(args)
        return jsonify({"measurements": list(measurements)})

    @fp.route("/api/measurements/grouped")
    @auth.login_required
    def getMeasurementsSummary():
        args = dict(request.args.items())
        measurements = config.collection.getSummary(args)
        return jsonify({"measurements": list(measurements)})

    @fp.route("/api/measurements/<measurementId>")
    @auth.login_required
    def getContext(measurementId):
        return jsonify(config.collection.get(measurementId))

    @fp.route("/api/measurements/timeseries/")
    @auth.login_required
    def getRequestsTimeseries():
        args = dict(request.args.items())
        return jsonify({"series": config.collection.getTimeseries(args)})

    @fp.route("/api/measurements/methodDistribution/")
    @auth.login_required
    def getMethodDistribution():
        args = dict(request.args.items())
        return jsonify({"distribution": config.collection.getMethodDistribution(args)})

    @fp.route("/db/dumpDatabase")
    @auth.login_required
    def dumpDatabase():
        response = jsonify({"summary": config.collection.getSummary()})
        response.headers["Content-Disposition"] = "attachment; filename=dump.json"
        return response

    @fp.route("/db/deleteDatabase")
    @auth.login_required
    def deleteDatabase():
        response = jsonify({"status": config.collection.truncate()})
        return response

    @fp.after_request
    def x_robots_tag_header(response):
        response.headers["X-Robots-Tag"] = "noindex, nofollow"
        return response

    app.register_blueprint(fp)


def read_config(app: Optional[Flask] = None):
    if app is None:
        app = current_app
    try:
        return (
            app.config.get("flask_profiler")
            or app.config.get("FLASK_PROFILER")
            or dict()
        )
    except RuntimeError:
        return {}


class Profiler:
    """Wrapper for extension."""

    def __init__(self, app=None):
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        config = Configuration(app)

        if not config.enabled:
            return

        wrapAppEndpoints(app)
        register_internal_routes(app)

        if not config.is_basic_auth_enabled:
            logging.warning(" * CAUTION: flask-profiler is working without basic auth!")


def sanatize_kwargs(kwargs):
    for key, value in list(kwargs.items()):
        if isinstance(value, UUID):
            kwargs[key] = str(value)
    return kwargs
