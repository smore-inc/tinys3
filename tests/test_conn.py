import unittest
from tinys3 import Conn
from tinys3.auth import S3Auth

TEST_SECRET_KEY = 'TEST_SECRET_KEY'
TEST_ACCESS_KEY = 'TEST_ACCESS_KEY'
TEST_BUCKET = 'bucket'


class TestConn(unittest.TestCase):
    def setUp(self):
        self.conn = Conn(TEST_SECRET_KEY, TEST_ACCESS_KEY, default_bucket=TEST_BUCKET, ssl=True)

    def test_creation(self):
        """
        Test the creation of a connection
        """

        self.assertIsInstance(self.conn.auth, S3Auth)
        self.assertEquals(self.conn.default_bucket, TEST_BUCKET)
        self.assertEquals(self.conn.ssl, True)

    def test_upload(self):
        """
        Test uploading
        """

        # Test a simple call

        # Test a call with a bucket

        # Test a call with all the params

    def test_delete(self):
        """
        Test delete
        """

        # Test with a bucket

        # Test without a bucket

    def test_copy(self):
        """
        Test copy
        """

        # Test with a target bucket

        # Test without a target bucket

    def test_update_metadata(self):
        """
        Test update_metadata
        """

        # Test with a bucket

        # Test without a bucket

    def test_list(self):
        """
        Test listing a bucket
        """