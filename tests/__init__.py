import unittest

import logging

import sys

from .test_endpoint_ignore import EndpointIgnoreTestCase
from .test_measurement import MeasurementTest
from .test_measure_endpoint import EndpointMeasurementTest, EndpointMeasurementTest2, JsonrpcMeasurementTest

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(MeasurementTest))
    suite.addTest(unittest.makeSuite(EndpointMeasurementTest))
    suite.addTest(unittest.makeSuite(EndpointIgnoreTestCase))
    suite.addTest(unittest.makeSuite(EndpointMeasurementTest2))
    suite.addTest(unittest.makeSuite(JsonrpcMeasurementTest))
    return suite
