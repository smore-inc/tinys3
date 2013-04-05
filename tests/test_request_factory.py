# -*- coding: utf-8 -*-
from datetime import timedelta
import mimetypes
import unittest
from tinys3.request_factory import RequestFactory

TEST_AUTH = ("TEST_SECRET_KEY", "TEST_ACCESS_KEY")


class TestRequestFactory(unittest.TestCase):
    def test_url_generation(self):
        """
        Check that the url generation function works properly
        """

        # Test the simplest url
        url = RequestFactory.bucket_url('test_key', 'test_bucket')
        self.assertEqual(url, 'http://s3.amazonaws.com/test_bucket/test_key', 'Simple url')

        # Simple with ssl
        url = RequestFactory.bucket_url('test_key', 'test_bucket', ssl=True)
        self.assertEqual(url, 'https://s3.amazonaws.com/test_bucket/test_key', 'Simple url with SSL')

        # Key with / prefix
        url = RequestFactory.bucket_url('/test_key', 'test_bucket')
        self.assertEqual(url, 'http://s3.amazonaws.com/test_bucket/test_key', 'Key with / prefix')

        # Nested key
        url = RequestFactory.bucket_url('folder/for/key/test_key', 'test_bucket')
        self.assertEqual(url, 'http://s3.amazonaws.com/test_bucket/folder/for/key/test_key', 'Nested key')

    def test_delete_request(self):
        """
        Test the generation of a delete request
        """

        r = RequestFactory.delete_request('key_to_delete', 'bucket', TEST_AUTH, ssl=True)

        self.assertEquals(r.auth, TEST_AUTH)
        self.assertEquals(r.method, 'DELETE')
        self.assertEquals(r.url, 'https://s3.amazonaws.com/bucket/key_to_delete')

    def test_update_metadata(self):
        """
        Test the generation of an update metadata request
        """
        r = RequestFactory.update_metadata_request('key_to_update', {'example-meta-key': 'example-meta-value'},
                                                   'bucket', True, TEST_AUTH, ssl=True)

        self.assertEquals(r.auth, TEST_AUTH)
        self.assertEquals(r.method, 'PUT')
        self.assertEquals(r.url, 'https://s3.amazonaws.com/bucket/key_to_update')

        # Test headers for copy information
        self.assertEquals(r.headers['x-amz-copy-source'], '/bucket/key_to_update')
        self.assertEquals(r.headers['x-amz-metadata-directive'], 'REPLACE')

        # Test for public headers
        self.assertEquals(r.headers['x-amz-acl'], 'public-read')

        # Test for extra metadata
        self.assertEquals(r.headers['example-meta-key'], 'example-meta-value')


    def test_copy(self):
        """
        Test the generation of a copy request
        """

        r = RequestFactory.copy_request('from_key', 'from_bucket', 'to_key', 'to_bucket', None, False, TEST_AUTH,
                                        ssl=True)

        self.assertEquals(r.auth, TEST_AUTH)
        self.assertEquals(r.method, 'PUT')
        self.assertEquals(r.url, 'https://s3.amazonaws.com/to_bucket/to_key')

        # Test headers for copy information
        self.assertEquals(r.headers['x-amz-copy-source'], '/from_bucket/from_key')
        # No metadata was given, metadata should be copied
        self.assertEquals(r.headers['x-amz-metadata-directive'], 'COPY')

        # Public was set to false, x-amz-acl should not be in the headers
        self.assertNotIn('x-amz-acl', r.headers)

    def test_simple_upload(self):
        """
        Test the simplest case of upload
        """
        r = RequestFactory.upload_request('upload_key', 'DUMMY_DATA', TEST_AUTH, 'bucket',
                                          ssl=True)

        self.assertEquals(r.auth, TEST_AUTH)
        self.assertEquals(r.method, 'PUT')
        self.assertEquals(r.url, 'https://s3.amazonaws.com/bucket/upload_key')

        # verify content type
        self.assertEquals(r.headers['Content-Type'], 'application/octet-stream')

        # verify public header
        self.assertEquals(r.headers['x-amz-acl'], 'public-read')

    def test_upload_content_type(self):
        """
        Test automatic/explicit content type setting
        """

        # No need to test fallback case ('application/octet-stream'), because
        # it was tested on the 'test_simple_upload' test

        # Test content type guessing
        r = RequestFactory.upload_request('test_zip_key.zip', 'DUMMY_DATA', TEST_AUTH, 'bucket')
        self.assertEquals(r.headers['Content-Type'], 'application/zip')

        # Test explicit content type
        r = RequestFactory.upload_request('test_zip_key.zip', 'DUMMY_DATA', TEST_AUTH, 'bucket',
                                          content_type='candy/smore')

        self.assertEquals(r.headers['Content-Type'], 'candy/smore')

    def test_upload_expires(self):
        """
        Test setting of expires headers
        """

        # Test max expiry headers
        r = RequestFactory.upload_request('test_zip_key.zip', 'DUMMY_DATA', TEST_AUTH, 'bucket',
                                          expires='max')

        self.assertEquals(r.headers['Cache-Control'], 'max-age=31536000, public')

        # Test number expiry
        r = RequestFactory.upload_request('test_zip_key.zip', 'DUMMY_DATA', TEST_AUTH, 'bucket',
                                          expires=1337)

        self.assertEquals(r.headers['Cache-Control'], 'max-age=1337, public')

        # Test timedelta expiry
        r = RequestFactory.upload_request('test_zip_key.zip', 'DUMMY_DATA', TEST_AUTH, 'bucket',
                                          expires=timedelta(weeks=2))

        self.assertEquals(r.headers['Cache-Control'], 'max-age=1209600, public')

    def test_upload_extra_headers(self):
        """
        Test providing extra headers to the upload request
        """

        r = RequestFactory.upload_request('test_zip_key.zip', 'DUMMY_DATA', TEST_AUTH, 'bucket',
                                          extra_headers={'example-meta-key': 'example-meta-value'})

        self.assertEquals(r.headers['example-meta-key'], 'example-meta-value')
