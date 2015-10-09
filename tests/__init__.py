import unittest


from .test_measurement import MeasurementTest
from .test_measure_endpoint import EndpointMeasurementTest


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(MeasurementTest))
    suite.addTest(unittest.makeSuite(EndpointMeasurementTest))
    return suite
