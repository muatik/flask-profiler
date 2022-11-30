# -*- coding: utf-8 -*-
import unittest

from flask_testing import TestCase as FlaskTestCase

from flask_profiler.flask_profiler import Configuration, DependencyInjector, is_ignored

from .basetest import BasetTest


class EndpointIgnoreTestCase(BasetTest, FlaskTestCase):
    def setUp(self) -> None:
        super().setUp()
        injector = DependencyInjector()
        self.controller = injector.get_filter_controller()

    def override_config(self, config):
        config["ignore"] = [r"^/static/.*", r"^/api/settings/\w+/secret/"]
        return config

    def test_01__is_ignored(self):
        ignored_routes = [
            "/static/file",
            "/static/",
            "/static/a/b/",
            "/api/settings/system/secret/",
            "/api/settings/common/secret/",
        ]

        for s in ignored_routes:
            self.assertEqual(is_ignored(s), True, "{} needs to be ignored.".format(s))

        not_ignored_routes = ["/static", "/api/static/", "/api/settings/system/name/"]

        for s in not_ignored_routes:
            self.assertEqual(is_ignored(s), False, "{} cannot be ignored.".format(s))

    def test_02_ignored_endpoints(self):
        config = Configuration(self.app)
        ignored_routes = [
            "/static/file",
            "/static/",
            "/static/a/b/",
            "/api/settings/system/name/",
        ]
        for s in ignored_routes:
            self.client.get(s)

        measurements = list(config.collection.filter(self.controller.parse_filter()))
        assert not measurements

        not_ignored_routes = ["/api/settings/personal/name/", "/api/static/"]
        for s in not_ignored_routes:
            print(self.client.get(s))

        measurements = list(config.collection.filter(self.controller.parse_filter()))
        self.assertEqual(len(measurements), 2)


if __name__ == "__main__":
    unittest.main()
