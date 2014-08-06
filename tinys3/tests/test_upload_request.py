from datetime import timedelta
import unittest
from flexmock import flexmock
from tinys3 import Connection
from tinys3.request_factory import UploadRequest


# Support for python 2/3
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO


class TestUploadRequest(unittest.TestCase):
    def setUp(self):
        """
        Create a default connection
        """
        self.conn = Connection("TEST_ACCESS_KEY", "TEST_SECRET_KEY", tls=True)

        self.dummy_data = StringIO('DUMMY_DATA')

    def _mock_adapter(self, request):
        """
        Creates a mock object and replace the result of the adapter method with is
        """
        mock_obj = flexmock()
        flexmock(request).should_receive('adapter').and_return(mock_obj)

        return mock_obj

    def test_simple_upload(self):
        """
        Test the simplest case of upload
        """

        r = UploadRequest(self.conn, 'upload_key', self.dummy_data, 'bucket')

        mock = self._mock_adapter(r)

        expected_headers = {
            'x-amz-acl': 'public-read',
            'Content-Type': 'application/octet-stream'
        }

        mock.should_receive('put').with_args(
            'https://bucket.s3.amazonaws.com/upload_key',
            # 'https://s3.amazonaws.com/bucket/upload_key',
            headers=expected_headers,
            data=self.dummy_data,
            auth=self.conn.auth
        ).and_return(self._mock_response()).once()

        r.run()

    def _mock_response(self):
        """
        Create a mock response with 'raise_for_status' method
        """

        return flexmock(raise_for_status=lambda: None)

    def test_upload_content_type(self):
        """
        Test automatic/explicit content type setting
        """

        # No need to test fallback case ('application/octet-stream'), because
        # it was tested on the 'test_simple_upload' test

        # Test auto content type guessing
        r = UploadRequest(self.conn, 'test_zip_key.zip', self.dummy_data, 'bucket')

        mock = self._mock_adapter(r)

        expected_headers = {
            'x-amz-acl': 'public-read',
            'Content-Type': 'application/zip'
        }

        mock.should_receive('put').with_args(
            #  'https://s3.amazonaws.com/bucket/test_zip_key.zip',
            'https://bucket.s3.amazonaws.com/test_zip_key.zip',
            headers=expected_headers,
            data=self.dummy_data,
            auth=self.conn.auth
        ).and_return(self._mock_response()).once()

        r.run()

        # Test explicit content setting
        r = UploadRequest(self.conn, 'test_zip_key.zip', self.dummy_data, 'bucket', content_type='candy/smore')

        mock = self._mock_adapter(r)

        expected_headers = {
            'x-amz-acl': 'public-read',
            'Content-Type': 'candy/smore'
        }

        mock.should_receive('put').with_args(
            # 'https://s3.amazonaws.com/bucket/test_zip_key.zip',
            'https://bucket.s3.amazonaws.com/test_zip_key.zip',
            headers=expected_headers,
            data=self.dummy_data,
            auth=self.conn.auth
        ).and_return(self._mock_response()).once()

        r.run()

    def test_upload_expires(self):
        """
        Test setting of expires headers
        """

        # Test max expiry headers

        r = UploadRequest(self.conn, 'test_zip_key.zip', self.dummy_data, 'bucket', expires='max')

        mock = self._mock_adapter(r)

        expected_headers = {
            'x-amz-acl': 'public-read',
            'Content-Type': 'application/zip',
            'Cache-Control': 'max-age=31536000, public'
        }

        mock.should_receive('put').with_args(
            'https://bucket.s3.amazonaws.com/test_zip_key.zip',
            # 'https://s3.amazonaws.com/bucket/test_zip_key.zip',
            headers=expected_headers,
            data=self.dummy_data,
            auth=self.conn.auth
        ).and_return(self._mock_response()).once()

        r.run()

        # Test number expiry
        r = UploadRequest(self.conn, 'test_zip_key.zip', self.dummy_data, 'bucket', expires=1337)

        mock = self._mock_adapter(r)

        expected_headers = {
            'x-amz-acl': 'public-read',
            'Content-Type': 'application/zip',
            'Cache-Control': 'max-age=1337, public'
        }

        mock.should_receive('put').with_args(
            # 'https://s3.amazonaws.com/bucket/test_zip_key.zip',
            'https://bucket.s3.amazonaws.com/test_zip_key.zip',
            headers=expected_headers,
            data=self.dummy_data,
            auth=self.conn.auth
        ).and_return(self._mock_response()).once()

        r.run()

        # Test timedelta expiry

        r = UploadRequest(self.conn, 'test_zip_key.zip', self.dummy_data, 'bucket', expires=timedelta(weeks=2))

        mock = self._mock_adapter(r)

        expected_headers = {
            'x-amz-acl': 'public-read',
            'Content-Type': 'application/zip',
            'Cache-Control': 'max-age=1209600, public'
        }

        mock.should_receive('put').with_args(
            # 'https://s3.amazonaws.com/bucket/test_zip_key.zip',
            'https://bucket.s3.amazonaws.com/test_zip_key.zip',
            headers=expected_headers,
            data=self.dummy_data,
            auth=self.conn.auth
        ).and_return(self._mock_response()).once()

        r.run()

    def test_upload_extra_headers(self):
        """
        Test providing extra headers to the upload request
        """

        r = UploadRequest(self.conn, 'test_zip_key.zip', self.dummy_data, 'bucket',
                          extra_headers={'example-meta-key': 'example-meta-value'})

        mock = self._mock_adapter(r)

        expected_headers = {
            'x-amz-acl': 'public-read',
            'Content-Type': 'application/zip',
            'example-meta-key': 'example-meta-value'
        }

        mock.should_receive('put').with_args(
            # 'https://s3.amazonaws.com/bucket/test_zip_key.zip',
            'https://bucket.s3.amazonaws.com/test_zip_key.zip',
            headers=expected_headers,
            data=self.dummy_data,
            auth=self.conn.auth
        ).and_return(self._mock_response()).once()

        r.run()

    def test_auto_close(self):
        """
        Test auto closing of the stream automatically
        """

        r = UploadRequest(self.conn, 'test_zip_key.zip', self.dummy_data, 'bucket',
                          close=True)

        mock = self._mock_adapter(r)

        expected_headers = {
            'x-amz-acl': 'public-read',
            'Content-Type': 'application/zip',
        }

        mock.should_receive('put').with_args(
            # 'https://s3.amazonaws.com/bucket/test_zip_key.zip',
            'https://bucket.s3.amazonaws.com/test_zip_key.zip',
            headers=expected_headers,
            data=self.dummy_data,
            auth=self.conn.auth
        ).and_return(self._mock_response()).once()

        r.run()

        self.assertTrue(self.dummy_data.closed)

    def test_auto_rewind(self):
        """
        Test auto rewinding of the input stream
        """

        # seek the data
        self.dummy_data.seek(5)

        r = UploadRequest(self.conn, 'test_zip_key.zip', self.dummy_data, 'bucket',
                          rewind=True)

        mock = self._mock_adapter(r)

        expected_headers = {
            'x-amz-acl': 'public-read',
            'Content-Type': 'application/zip',
        }

        mock.should_receive('put').with_args(
            # 'https://s3.amazonaws.com/bucket/test_zip_key.zip',
            'https://bucket.s3.amazonaws.com/test_zip_key.zip',
            headers=expected_headers,
            data=self.dummy_data,
            auth=self.conn.auth
        ).and_return(self._mock_response()).once()

        r.run()

        self.assertEqual(self.dummy_data.tell(), 0)
