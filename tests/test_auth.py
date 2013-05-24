# -*- coding: utf-8 -*-
from __future__ import print_function, absolute_import, unicode_literals

import unittest
from flexmock import flexmock
from tinys3.auth import S3Auth

from requests import Request

# Test access and secret keys, from the s3 manual on REST authentication
# http://docs.aws.amazon.com/AmazonS3/latest/dev/RESTAuthentication.html
TEST_ACCESS_KEY = 'AKIAIOSFODNN7EXAMPLE'
TEST_SECRET_KEY = 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY'


class TestS3Auth(unittest.TestCase):
    def setUp(self):
        # Create a new auth object for every test
        self.auth = S3Auth(TEST_ACCESS_KEY, TEST_SECRET_KEY)

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

    def test_x_amz_date(self):
        mock_request = Request(method='DELETE',
                               url="http://s3.amazonaws.com/johnsmith/photos/puppy.jpg",
                               headers={'Date': 'Tue, 27 Mar 2007 21:20:27 +0000',
                                        'x-amz-date': 'Tue, 27 Mar 2007 21:20:26 +0000'})

        target = """
DELETE



x-amz-date:Tue, 27 Mar 2007 21:20:26 +0000
/johnsmith/photos/puppy.jpg
""".strip()

        self.assertEquals(self.auth.string_to_sign(mock_request), target)


    def test_delete(self):
        mock_request = Request(method='DELETE',
                               url="http://s3.amazonaws.com/johnsmith/photos/puppy.jpg",
                               headers={'Date': 'Tue, 27 Mar 2007 21:20:26 +0000'})

        target = """
DELETE


Tue, 27 Mar 2007 21:20:26 +0000
/johnsmith/photos/puppy.jpg
""".strip()

        self.assertEquals(self.auth.string_to_sign(mock_request), target)

        # Call auth
        self.auth(mock_request)

        # test authorization code
        self.assertEquals(mock_request.headers['Authorization'],
                          'AWS AKIAIOSFODNN7EXAMPLE:lx3byBScXR6KzyMaifNkardMwNk=')

    def test_upload(self):
        mock_request = Request(method='PUT',
                               url="http://static.johnsmith.net:8080/db-backup.dat.gz",
                               headers={'Date': 'Tue, 27 Mar 2007 21:06:08 +0000',
                                        'x-amz-acl': 'public-read',
                                        'content-type': 'application/x-download',
                                        'Content-MD5': '4gJE4saaMU4BqNR0kLY+lw==',
                                        'X-Amz-Meta-ReviewedBy': 'joe@johnsmith.net,jane@johnsmith.net',
                                        'X-Amz-Meta-FileChecksum': '0x02661779',
                                        'X-Amz-Meta-ChecksumAlgorithm': 'crc32',
                                        'Content-Disposition': 'attachment; filename=database.dat',
                                        'Content-Encoding': 'gzip',
                                        'Content-Length': '5913339'})

        target = """
PUT
4gJE4saaMU4BqNR0kLY+lw==
application/x-download
Tue, 27 Mar 2007 21:06:08 +0000
x-amz-acl:public-read
x-amz-meta-checksumalgorithm:crc32
x-amz-meta-filechecksum:0x02661779
x-amz-meta-reviewedby:joe@johnsmith.net,jane@johnsmith.net
/static.johnsmith.net/db-backup.dat.gz
        """.strip()

        self.assertEquals(self.auth.string_to_sign(mock_request), target)

        # Call auth
        self.auth(mock_request)

        # test authorization code
        self.assertEquals(mock_request.headers['Authorization'],
                          'AWS AKIAIOSFODNN7EXAMPLE:ilyl83RwaSoYIEdixDQcA4OnAnc=')

    def test_upload_0_length_file(self):
        """
        Make sure the auth adds content-length: 0 if we don't have any content length defined (for put requests)
        """

        mock_request = Request(method='PUT',
                               url="http://static.johnsmith.net:8080/db-backup.dat.gz",
                               headers={'Date': 'Tue, 27 Mar 2007 21:06:08 +0000',
                                        'x-amz-acl': 'public-read',
                                        'Content-type': 'application/x-download'})
        # Call auth
        self.auth(mock_request)

        # test Content-Length
        self.assertEquals(mock_request.headers['Content-Length'], '0')

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

    def test_simple_signature(self):
        self.auth = S3Auth('AKID', 'secret')
        mock_request = Request(method='POST', url='/', headers={'Date': 'DATE-STRING'})

        flexmock(self.auth).should_receive('string_to_sign').and_return('string-to-sign')

        self.auth(mock_request)

        self.assertEquals(mock_request.headers['Authorization'], 'AWS AKID:Gg5WLabTOvH0WMd15wv7lWe4zK0=')


    def test_string_to_sign(self):
        mock_request = Request(method='POST', url='/', headers={'Date': 'DATE-STRING'})

        target = """
POST


DATE-STRING
/
""".strip()

        self.assertEquals(self.auth.string_to_sign(mock_request), target)

    def test_sts_includes_content_md5_and_content_type(self):
        mock_request = Request(method='POST', url='/',
                               headers={'Date': 'DATE-STRING',
                                        'Content-Type': 'CONTENT-TYPE',
                                        'Content-MD5': 'CONTENT-MD5'})

        target = """
POST
CONTENT-MD5
CONTENT-TYPE
DATE-STRING
/
""".strip()

        self.assertEquals(self.auth.string_to_sign(mock_request), target)

    def test_sts_includes_the_http_method(self):
        mock_request = Request(method='VERB', url='/',
                               headers={'Date': 'DATE-STRING'})

        target = """
VERB


DATE-STRING
/
""".strip()

        self.assertEquals(self.auth.string_to_sign(mock_request), target)


    def test_sts_includes_any_x_amz_headers_but_not_others(self):
        mock_request = Request(method='POST', url='/',
                               headers={'Date': 'DATE-STRING',
                                        'X-Amz-Abc': 'abc',
                                        'X-Amz-Xyz': 'xyz',
                                        'random-header': 'random'})

        target = """
POST


DATE-STRING
x-amz-abc:abc
x-amz-xyz:xyz
/
""".strip()

        self.assertEquals(self.auth.string_to_sign(mock_request), target)

    def test_sts_includes_x_amz_headers_that_are_lower_cased(self):
        mock_request = Request(method='POST', url='/',
                               headers={'Date': 'DATE-STRING',
                                        'x-amz-Abc': 'abc',
                                        'x-amz-Xyz': 'xyz',
                                        'random-header': 'random'})

        target = """
POST


DATE-STRING
x-amz-abc:abc
x-amz-xyz:xyz
/
""".strip()

        self.assertEquals(self.auth.string_to_sign(mock_request), target)

    def test_sts_sorts_headers_by_their_name(self):
        mock_request = Request(method='POST', url='/',
                               headers={'Date': 'DATE-STRING',
                                        'x-amz-Abc': 'abc',
                                        'x-amz-Xyz': 'xyz',
                                        'x-amz-mno': 'mno',
                                        'random-header': 'random'})

        target = """
POST


DATE-STRING
x-amz-abc:abc
x-amz-mno:mno
x-amz-xyz:xyz
/
""".strip()

        self.assertEquals(self.auth.string_to_sign(mock_request), target)

    def test_sts_builds_a_canonical_resource_from_the_path(self):
        mock_request = Request(method='POST', url='/bucket_name/key',
                               headers={'Date': 'DATE-STRING'})

        target = """
POST


DATE-STRING
/bucket_name/key
""".strip()

        self.assertEquals(self.auth.string_to_sign(mock_request), target)

    def test_sts_appends_the_bucket_to_the_path_when_it_is_part_of_the_hostname(self):
        mock_request = Request(method='POST', url='http://bucket-name.s3.amazonaws.com/',
                               headers={'Date': 'DATE-STRING'})

        target = """
POST


DATE-STRING
/bucket-name/
""".strip()

        self.assertEquals(self.auth.string_to_sign(mock_request), target)

    def test_sts_appends_the_subresource_portion_of_the_path_querystring(self):
        mock_request = Request(method='POST', url='http://bucket-name.s3.amazonaws.com/?acl',
                               headers={'Date': 'DATE-STRING'})

        target = """
POST


DATE-STRING
/bucket-name/?acl
""".strip()

        self.assertEquals(self.auth.string_to_sign(mock_request), target)

    def test_sts_includes_sub_resource_value_when_present(self):
        mock_request = Request(method='POST', url='/bucket_name/key?versionId=123',
                               headers={'Date': 'DATE-STRING'})

        target = """
POST


DATE-STRING
/bucket_name/key?versionId=123
""".strip()

        self.assertEquals(self.auth.string_to_sign(mock_request), target)

    def test_sts_omits_non_sub_resource_querystring_params_from_the_resource_string(self):
        mock_request = Request(method='POST', url='/?versionId=abc&next-marker=xyz',
                               headers={'Date': 'DATE-STRING'})

        target = """
POST


DATE-STRING
/?versionId=abc
""".strip()

        self.assertEquals(self.auth.string_to_sign(mock_request), target)

    #
    #     def test_sts_sorts_sub_resources_by_name(self):
    #         mock_request = Request(method='POST', url='/?logging&acl&website&torrent=123',
    #                                headers={'Date': 'DATE-STRING'})
    #
    #         target = """
    # POST
    #
    #
    # DATE-STRING
    # /?acl&logging&torrent=123&website
    # """.strip()
    #
    #         self.assertEquals(self.auth.string_to_sign(mock_request), target)

    def test_sts_includes_the_un_decoded_query_string_param_for_sub_resources(self):
        mock_request = Request(method='POST', url='/?versionId=a%2Bb',
                               headers={'Date': 'DATE-STRING'})

        target = """
POST


DATE-STRING
/?versionId=a%2Bb
""".strip()

        self.assertEquals(self.auth.string_to_sign(mock_request), target)

        #

#     def test_sts_includes_the_non_encoded_query_string_get_header_overrides(self):
#         mock_request = Request(method='POST', url='/?response-content-type=a%2Bb',
#                                headers={'Date': 'DATE-STRING'})
#
#         target = """
# POST
#
#
# DATE-STRING
# /?response-content-type=a+b
# """.strip()
#
#         self.assertEquals(self.auth.string_to_sign(mock_request), target)
