# -*- coding: utf-8 -*-
import unittest
from tinys3.auth import S3Auth

from requests import Request

# Test access and secret keys, from the s3 manual on REST authentication
# http://docs.aws.amazon.com/AmazonS3/latest/dev/RESTAuthentication.html
TEST_ACCESS_KEY = 'AKIAIOSFODNN7EXAMPLE'
TEST_SECRET_KEY = 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY'


class TestS3Auth(unittest.TestCase):
    def setUp(self):
        # Create a new auth object for every test
        self.auth = S3Auth(TEST_SECRET_KEY, TEST_ACCESS_KEY)

    def test_object_get(self):
        mock_request = Request(method='GET',
                               url="http://johnsmith.s3.amazonaws.com/photos/puppy.jpg",
                               headers={'Date': 'Tue, 27 Mar 2007 19:36:42 +0000'})

        # Call auth
        self.auth(mock_request)

        # test authorization code
        self.assertEquals(mock_request.headers['Authorization'],
                          'AWS AKIAIOSFODNN7EXAMPLE:bWq2s1WEIj+Ydj0vQ697zp+IXMU=')

    def test_object_put(self):
        mock_request = Request(method='PUT',
                               url="http://johnsmith.s3.amazonaws.com/photos/puppy.jpg",
                               headers={'Date': 'Tue, 27 Mar 2007 21:15:45 +0000',
                                        'Content-Type': 'image/jpeg',
                                        'Content-Length': 94328})

        # Call auth
        self.auth(mock_request)

        # test authorization code
        self.assertEquals(mock_request.headers['Authorization'],
                          'AWS AKIAIOSFODNN7EXAMPLE:MyyxeRY7whkBe+bq8fHCL/2kKUg=')

    def test_list_reqeust(self):
        mock_request = Request(method='GET',
                               url="http://johnsmith.s3.amazonaws.com/?prefix=photos&max-keys=50&marker=puppy",
                               headers={'Date': 'Tue, 27 Mar 2007 19:42:41 +0000'})

        # Call auth
        self.auth(mock_request)

        # test authorization code
        self.assertEquals(mock_request.headers['Authorization'],
                          'AWS AKIAIOSFODNN7EXAMPLE:htDYFYduRNen8P9ZfE/s9SuKy0U=')

    def test_fetch(self):
        mock_request = Request(method='GET',
                               url="http://johnsmith.s3.amazonaws.com/?acl",
                               headers={'Date': 'Tue, 27 Mar 2007 19:44:46 +0000'})

        # Call auth
        self.auth(mock_request)

        # test authorization code
        self.assertEquals(mock_request.headers['Authorization'],
                          'AWS AKIAIOSFODNN7EXAMPLE:c2WLPFtWHVgbEmeEG93a4cG37dM=')

    def test_delete(self):
        mock_request = Request(method='DELETE',
                               url="http://s3.amazonaws.com/johnsmith/photos/puppy.jpg",
                               headers={'Date': 'Tue, 27 Mar 2007 21:20:27 +0000',
                                        'x-amz-date': 'Tue, 27 Mar 2007 21:20:26 +0000'})

        # Call auth
        self.auth(mock_request)

        # test authorization code
        self.assertEquals(mock_request.headers['Authorization'],
                          'AWS AKIAIOSFODNN7EXAMPLE:9b2sXq0KfxsxHtdZkzx/9Ngqyh8=')

    def test_upload(self):
        mock_request = Request(method='PUT',
                               url="http://static.johnsmith.net:8080/db-backup.dat.gz",
                               headers={'Date': 'Tue, 27 Mar 2007 21:06:08 +0000',
                                        'x-amz-acl': 'public-read',
                                        'content-type': 'application/x-download',
                                        'Content-MD5': '4gJE4saaMU4BqNR0kLY+lw==',
                                        'X-Amz-Meta-ReviewedBy': 'joe@johnsmith.net,jane@jhonsmith.net',
                                        'X-Amz-Meta-FileChecksum': '0x02661779',
                                        'X-Amz-Meta-ChecksumAlgorithm': 'crc32',
                                        'Content-Disposition': 'attachment; filename=database.dat',
                                        'Content-Encoding': 'gzip',
                                        'Content-Length': '5913339'})

        # Call auth
        self.auth(mock_request)

        # test authorization code
        self.assertEquals(mock_request.headers['Authorization'],
                          'AWS AKIAIOSFODNN7EXAMPLE:ilyl83RwaSoYIEdixDQcA4OnAnc=')

    def test_list_all_buckets(self):
        mock_request = Request(method='GET',
                               url="http://s3.amazonaws.com",
                               headers={'Date': 'Wed, 28 Mar 2007 01:29:59 +0000'})

        # Call auth
        self.auth(mock_request)

        # test authorization code
        self.assertEquals(mock_request.headers['Authorization'],
                          'AWS AKIAIOSFODNN7EXAMPLE:qGdzdERIC03wnaRNKh6OqZehG9s=')

    def test_unicode_keys(self):
        mock_request = Request(method='GET',
                               url="http://s3.amazonaws.com/dictionary/fran%C3%A7ais/pr%c3%a9f%c3%a8re",
                               headers={'Date': 'Wed, 28 Mar 2007 01:49:49 +0000'})

        # Call auth
        self.auth(mock_request)

        # test authorization code
        self.assertEquals(mock_request.headers['Authorization'],
                          'AWS AKIAIOSFODNN7EXAMPLE:DNEZGsoieTZ92F3bUfSPQcbGmlM=')
