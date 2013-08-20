# -*- coding: utf-8 -*-

import unittest
from tinys3 import Connection
from tinys3.auth import S3Auth
from flexmock import flexmock

TEST_SECRET_KEY = 'TEST_SECRET_KEY'
TEST_ACCESS_KEY = 'TEST_ACCESS_KEY'
TEST_BUCKET = 'bucket'
TEST_DATA = 'test test test' * 2


class TestConn(unittest.TestCase):
    def setUp(self):
        self.conn = Connection(TEST_ACCESS_KEY,TEST_SECRET_KEY, default_bucket=TEST_BUCKET, tls=True)

    def test_creation(self):
        """
        Test the creation of a connection
        """

        self.assertTrue(isinstance(self.conn.auth, S3Auth))
        self.assertEquals(self.conn.default_bucket, TEST_BUCKET)
        self.assertEquals(self.conn.tls, True)
        self.assertEquals(self.conn.endpoint, "s3.amazonaws.com")
