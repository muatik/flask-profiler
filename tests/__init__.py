import logging
import sys
import unittest

from .test_endpoint_ignore import EndpointIgnoreTestCase
from .test_measure_endpoint import EndpointMeasurementTest, EndpointMeasurementTest2
from .test_measurement import MeasurementTest

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(MeasurementTest))
    suite.addTest(unittest.makeSuite(EndpointMeasurementTest))
    suite.addTest(unittest.makeSuite(EndpointIgnoreTestCase))
    suite.addTest(unittest.makeSuite(EndpointMeasurementTest2))
    return suite
