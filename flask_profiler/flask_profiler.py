# -*- coding: utf-8 -*-

import functools
import logging
import re
import time
from typing import Callable, Optional, TypeVar, Union, cast
from uuid import UUID

from flask import Blueprint, Flask
from flask import Response as FlaskResponse
from flask import current_app, jsonify, request
from flask_httpauth import HTTPBasicAuth

from .configuration import Configuration
from .controllers.filter_controller import FilterController
from .presenters.filtered_presenter import FilteredPresenter
from .presenters.summary_presenter import SummaryPresenter
from .storage.base import Measurement, RequestMetadata

ResponseT = Union[str, FlaskResponse]
logger = logging.getLogger("flask-profiler")
auth = HTTPBasicAuth()
Route = TypeVar("Route", bound=Callable[..., ResponseT])


flask_profiler = Blueprint(
    "flask_profiler",
    __name__,
    static_folder="static/dist/",
    static_url_path="/static/dist",
)


@auth.verify_password
def verify_password(username, password):
    injector = DependencyInjector()
    config = injector.get_configuration()
    if not config.is_basic_auth_enabled:
        return True

    if (
        username == config.basic_auth_username
        and password == config.basic_auth_password
    ):
        return True
    logging.warning("flask-profiler authentication failed")
    return False


@flask_profiler.route("/")
@auth.login_required
def index() -> ResponseT:
    return flask_profiler.send_static_file("index.html")


@flask_profiler.route("/api/measurements/")
@auth.login_required
def filterMeasurements() -> ResponseT:
    injector = DependencyInjector()
    controller = injector.get_filter_controller()
    presenter = injector.get_filtered_presenter()
    config = injector.get_configuration()
    args = dict(request.args.items())
    query = controller.parse_filter(args)
    measurements = config.collection.filter(query)
    view_model = presenter.present_filtered_measurements(measurements)
    return jsonify(view_model)


@flask_profiler.route("/api/measurements/grouped")
@auth.login_required
def getMeasurementsSummary() -> ResponseT:
    injector = DependencyInjector()
    controller = injector.get_filter_controller()
    presenter = injector.get_summary_presenter()
    config = injector.get_configuration()
    args = dict(request.args.items())
    query = controller.parse_filter(args)
    measurements = config.collection.getSummary(query)
    view_model = presenter.present_summaries(measurements)
    return jsonify(view_model)


@flask_profiler.route("/api/measurements/<measurementId>")
@auth.login_required
def getContext(measurementId) -> ResponseT:
    injector = DependencyInjector()
    config = injector.get_configuration()
    return jsonify(config.collection.get(measurementId))


@flask_profiler.route("/api/measurements/timeseries/")
@auth.login_required
def getRequestsTimeseries() -> ResponseT:
    injector = DependencyInjector()
    config = injector.get_configuration()
    args = dict(request.args.items())
    return jsonify(
        {
            "series": config.collection.getTimeseries(
                startedAt=float(args.get("startedAt", time.time() - 3600 * 24 * 7)),
                endedAt=float(args.get("endedAt", time.time())),
                interval=args.get("interval", "hourly"),
            )
        }
    )


@flask_profiler.route("/api/measurements/methodDistribution/")
@auth.login_required
def getMethodDistribution() -> ResponseT:
    injector = DependencyInjector()
    config = injector.get_configuration()
    args = dict(request.args.items())
    return jsonify(
        {
            "distribution": config.collection.getMethodDistribution(
                startedAt=float(args.get("startedAt", time.time() - 3600 * 24 * 7)),
                endedAt=float(args.get("endedAt", time.time())),
            )
        }
    )


@flask_profiler.route("/db/deleteDatabase")
@auth.login_required
def deleteDatabase() -> ResponseT:
    injector = DependencyInjector()
    config = injector.get_configuration()
    response = jsonify({"status": config.collection.truncate()})
    return response


@flask_profiler.after_request
def x_robots_tag_header(response) -> FlaskResponse:
    response.headers["X-Robots-Tag"] = "noindex, nofollow"
    return response


def is_ignored(name: str) -> bool:
    injector = DependencyInjector()
    config = injector.get_configuration()
    for pattern in config.ignore_patterns:
        if re.search(pattern, name):
            return True
    return False


def measure(f: Route, name: str, method: str, context: RequestMetadata) -> Route:
    injector = DependencyInjector()
    config = injector.get_configuration()
    logger.debug("{0} is being processed.")
    if is_ignored(name):
        logger.debug("{0} is ignored.")
        return f

    @functools.wraps(f)
    def wrapper(*args, **kwargs) -> ResponseT:
        if not config.sampling_function():
            return f(*args, **kwargs)
        started_at = time.time()
        try:
            returnVal = f(*args, **kwargs)
        finally:
            stopped_at = time.time()
            measurement = Measurement(
                method=method,
                context=context,
                name=name,
                args=list(map(str, args)),
                kwargs=sanatize_kwargs(kwargs),
                startedAt=started_at,
                endedAt=stopped_at,
            )
            logger.debug(str(measurement.serialize_to_json()))
            config.collection.insert(measurement)
        return returnVal

    return cast(Route, wrapper)


def wrapHttpEndpoint(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        context = RequestMetadata(
            url=request.base_url,
            args=dict(request.args.items()),
            form=dict(request.form.items()),
            headers=dict(request.headers.items()),
            endpoint_name=request.endpoint,
            client_address=request.remote_addr,
        )
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


def init_app(app: Flask) -> None:
    """Initialize the flask-profiler package with your flask app.
    Unless flask-profiler is explicityly enabled in the flask config
    this will do nothing.

    Initialization must be one after all routes you want to monitor
    are registered with your app.

    """
    injector = DependencyInjector(app=app)
    config = injector.get_configuration()

    if not config.enabled:
        return

    wrapAppEndpoints(app)
    app.register_blueprint(flask_profiler, url_prefix="/" + config.url_prefix)

    if not config.is_basic_auth_enabled:
        logging.warning(" * CAUTION: flask-profiler is working without basic auth!")


def sanatize_kwargs(kwargs):
    for key, value in list(kwargs.items()):
        if isinstance(value, UUID):
            kwargs[key] = str(value)
    return kwargs


class SystemClock:
    def get_epoch(self) -> float:
        return time.time()


class DependencyInjector:
    def __init__(self, *, app: Optional[Flask] = None) -> None:
        self.app = app or current_app

    def get_clock(self) -> SystemClock:
        return SystemClock()

    def get_filter_controller(self) -> FilterController:
        return FilterController(clock=self.get_clock())

    def get_configuration(self) -> Configuration:
        return Configuration(self.app)

    def get_summary_presenter(self) -> SummaryPresenter:
        return SummaryPresenter()

    def get_filtered_presenter(self) -> FilteredPresenter:
        return FilteredPresenter()
