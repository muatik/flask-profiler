# -*- coding: utf-8 -*-
import unittest

from flask_testing import TestCase as FlaskTestCase

from flask_profiler.flask_profiler import is_ignored
from .basetest import BasetTest, flask_profiler


class EndpointIgnoreTestCase(BasetTest, FlaskTestCase):

    def tearDown(self):
        pass

    def test_01__is_ignored(self):
        conf = {
            "ignore": [
                "^/static/.*",
                "^/api/settings/\w+/secret/"
            ]
        }

        ignored_routes = [
            "/static/file",
            "/static/",
            "/static/a/b/",
            "/api/settings/system/secret/",
            "/api/settings/common/secret/"
        ]

        for s in ignored_routes:
            self.assertEqual(is_ignored(s, conf), True, "{} needs to be ignored.".format(s))

        not_ignored_routes = [
            "/static",
            "/api/static/",
            "/api/settings/system/name/"
        ]

        for s in not_ignored_routes:
            self.assertEqual(is_ignored(s, conf), False, "{} cannot be ignored.".format(s))

    def test_02_ignored_endpoints(self):
        ignored_routes = [
            "/static/file",
            "/static/",
            "/static/a/b/",
            "/api/settings/system/name/"
        ]
        for s in ignored_routes:
            self.client.get(s)

        measurements = list(flask_profiler.collection.filter())
        self.assertEqual(len(measurements), 0)

        not_ignored_routes = [
            "/api/settings/personal/name/",
            "/api/static/"
        ]
        for s in not_ignored_routes:
            print(self.client.get(s))

        measurements = list(flask_profiler.collection.filter())
        self.assertEqual(len(measurements), 2)


if __name__ == '__main__':
    unittest.main()
