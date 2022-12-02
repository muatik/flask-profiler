from typing import List, Optional

from flask import Flask, g

from .storage.base import BaseStorage
from .storage.sqlite import Sqlite


class Configuration:
    def __init__(self, app: Flask) -> None:
        self.app = app

    @property
    def enabled(self) -> bool:
        return self.read_config().get("enabled", False)

    def sampling_function(self) -> bool:
        config = self.read_config()
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
        return self.read_config().get("ignore", [])

    @property
    def verbose(self) -> bool:
        return self.read_config().get("verbose", False)

    @property
    def url_prefix(self) -> str:
        return self.read_config().get("endpointRoot", "flask-profiler")

    @property
    def is_basic_auth_enabled(self) -> bool:
        return self.read_config().get("basicAuth", {}).get("enabled", False)

    @property
    def basic_auth_username(self) -> str:
        return self.read_config()["basicAuth"]["username"]

    @property
    def basic_auth_password(self) -> str:
        return self.read_config()["basicAuth"]["passwordb"]

    @property
    def collection(self) -> BaseStorage:
        collection = g.get("flask_profiler_collection")
        if collection is None:
            collection = self._create_storage()
            g.flask_profiler_collection = collection
        return collection

    def _create_storage(self) -> BaseStorage:
        conf = self.read_config().get("storage", {})
        return Sqlite(
            sqlite_file=conf.get("FILE", "flask_profiler.sql"),
            table_name=conf.get("TABLE", "measurements"),
        )

    def read_config(self):
        return (
            self.app.config.get("flask_profiler")
            or self.app.config.get("FLASK_PROFILER")
            or dict()
        )
