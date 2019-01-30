# -*- coding: utf8 -*-
import unittest
import uuid

from flask_testing import TestCase as FlaskTestCase

from .basetest import BasetTest


class EndpointUuidTest(BasetTest, FlaskTestCase):
    
    def test_01_proper_status(self):
        uuid_param = str(uuid.uuid4())
        response = self.client.get("/api/uuid/{}".format(uuid_param))
        self.assertEqual(response.status_code, 200)



if __name__ == '__main__':
    unittest.main()
