import unittest
from tinys3 import Conn
from tinys3.auth import S3Auth
from tinys3.request_factory import RequestFactory
from flexmock import flexmock

TEST_SECRET_KEY = 'TEST_SECRET_KEY'
TEST_ACCESS_KEY = 'TEST_ACCESS_KEY'
TEST_BUCKET = 'bucket'
TEST_DATA = 'test test test' * 2


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

        flexmock(self.conn).should_receive('run')
        mock_factory = flexmock(RequestFactory)

        # Test a simple call
        mock_factory.should_receive('upload_request') \
            .with_args('test_key', TEST_DATA, bucket=TEST_BUCKET,
                       auth=self.conn.auth, expires=None, content_type=None,
                       public=True, extra_headers=None, ssl=True)

        self.conn.upload('test_key', TEST_DATA)

        # Test a call with a bucket
        mock_factory.should_receive('upload_request') \
            .with_args('test_key', TEST_DATA, bucket='special_bucket',
                       auth=self.conn.auth, expires=None, content_type=None,
                       public=True, extra_headers=None, ssl=True)

        self.conn.upload('test_key', TEST_DATA, 'special_bucket')

        # Test a call with all the params

        mock_factory.should_receive('upload_request') \
            .with_args('test_key', TEST_DATA, bucket='special_bucket',
                       auth=self.conn.auth, expires='max', content_type='application/zip',
                       public=False, extra_headers={'test': 'value'}, ssl=True)

        self.conn.upload('test_key', TEST_DATA, 'special_bucket',
                         expires='max', content_type='application/zip', public=False, headers={'test': 'value'})

    def test_delete(self):
        """
        Test delete
        """

        # Test with a bucket

        flexmock(self.conn).should_receive('run')
        mock_factory = flexmock(RequestFactory)

        mock_factory.should_receive('delete_request') \
            .with_args('test_key', 'special_bucket',
                       auth=self.conn.auth, ssl=True)

        self.conn.delete('test_key', 'special_bucket')

        # Test without a bucket
        mock_factory.should_receive('delete_request') \
            .with_args('test_key', TEST_BUCKET,
                       auth=self.conn.auth, ssl=True)

        self.conn.delete('test_key')

    def test_copy(self):
        """
        Test copy
        """

        flexmock(self.conn).should_receive('run')
        mock_factory = flexmock(RequestFactory)

        # Test with a target bucket
        mock_factory.should_receive('copy_request') \
            .with_args('from_key', 'from_bucket', 'to_key', 'to_bucket', None, True,
                       auth=self.conn.auth, ssl=True)

        self.conn.copy('from_key', 'from_bucket', 'to_key', 'to_bucket')

        # Test without a target bucket
        mock_factory.should_receive('copy_request') \
            .with_args('from_key', 'from_bucket', 'to_key', 'from_bucket', None, True,
                       auth=self.conn.auth, ssl=True)

        self.conn.copy('from_key', 'from_bucket', 'to_key')

        # test with metadata
        # Test without a target bucket
        mock_factory.should_receive('copy_request') \
            .with_args('from_key', 'from_bucket', 'to_key', 'to_bucket', {'m': 'v'}, False,
                       auth=self.conn.auth, ssl=True)

        self.conn.copy('from_key', 'from_bucket', 'to_key', 'to_bucket', metadata={'m': 'v'},
                       public=False)

    def test_update_metadata(self):
        """
        Test update_metadata
        """

        flexmock(self.conn).should_receive('run')
        mock_factory = flexmock(RequestFactory)

        # Test with a bucket
        mock_factory.should_receive('update_metadata_request') \
            .with_args('key', {'m': 'v'}, 'special_bucket', public=True,
                       auth=self.conn.auth, ssl=True)

        self.conn.update_metadata('key', {'m': 'v'}, 'special_bucket')

        # Test without a bucket
        mock_factory.should_receive('update_metadata_request') \
            .with_args('key', {'m': 'v'}, TEST_BUCKET, public=True,
                       auth=self.conn.auth, ssl=True)

        self.conn.update_metadata('key', {'m': 'v'})

    def test_list(self):
        """
        Test listing a bucket
        """