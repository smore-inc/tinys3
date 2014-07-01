# -*- coding: utf-8 -*-
import datetime
import unittest
from flexmock import flexmock
from tinys3.request_factory import ListRequest
from tinys3 import Connection


class TestNonUploadRequests(unittest.TestCase):
    def setUp(self):
        self.conn = Connection("TEST_ACCESS_KEY", "TEST_SECRET_KEY", tls=True)
        self.r = ListRequest(self.conn, 'prefix', 'bucket')
        
        self.adapter = flexmock()
        flexmock(self.r).should_receive('adapter').and_return(self.adapter)

    def test_simple_list_request(self):
        """
        Test the generation of a list request
        """

        self.adapter.should_receive('get').with_args(
            'https://s3.amazonaws.com/bucket/',
            auth=self.conn.auth,
            params={'prefix': 'prefix', 'marker': ''},
        ).and_return(flexmock(raise_for_status=lambda: None, content=b"""
            <?xml version="1.0" encoding="UTF-8"?>
            <ListBucketResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/">
                <Name>bucket</Name>
                <Prefix>prefix</Prefix>
                <Marker></Marker>
                <MaxKeys>1000</MaxKeys>
                <IsTruncated>false</IsTruncated>
                <Contents>
                    <Key>prefix/file1</Key>
                    <LastModified>2013-10-31T15:38:32.000Z</LastModified>
                    <ETag>&quot;d41d8cd98f00b204e9800998ecf8427e&quot;</ETag>
                    <Size>0</Size>
                    <StorageClass>STANDARD</StorageClass>
                </Contents>
                <Contents>
                    <Key>prefix/file2</Key>
                    <LastModified>2014-06-16T15:58:56.000Z</LastModified>
                    <ETag>&quot;31ed785816f1162fca532cbc80b27266&quot;</ETag>
                    <Size>581708</Size>
                    <StorageClass>STANDARD</StorageClass>
                </Contents>
            </ListBucketResult>
        """.strip())).once()

        self.assertEquals(list(self.r.run()), [{
            'etag': 'd41d8cd98f00b204e9800998ecf8427e',
            'key': 'prefix/file1',
            'last_modified': datetime.datetime(2013, 10, 31, 15, 38, 32),
            'size': 0,
            'storage_class': 'STANDARD',
        }, {
            'etag': '31ed785816f1162fca532cbc80b27266',
            'key': 'prefix/file2',
            'last_modified': datetime.datetime(2014, 6, 16, 15, 58, 56),
            'size': 581708,
            'storage_class': 'STANDARD',
        }])

    def test_chained_list_requests(self):
        """
        Test the generation of a more complex list request
        """

        self.adapter.should_receive('get').with_args(
            'https://s3.amazonaws.com/bucket/',
            auth=self.conn.auth,
            params={'prefix': 'prefix', 'marker': ''},
        ).and_return(flexmock(raise_for_status=lambda: None, content=b"""
            <?xml version="1.0" encoding="UTF-8"?>
            <ListBucketResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/">
                <Name>bucket</Name>
                <Prefix>prefix</Prefix>
                <Marker></Marker>
                <MaxKeys>1000</MaxKeys>
                <IsTruncated>true</IsTruncated>
                <Contents>
                    <Key>prefix/file1</Key>
                    <LastModified>2013-10-31T15:38:32.000Z</LastModified>
                    <ETag>&quot;d41d8cd98f00b204e9800998ecf8427e&quot;</ETag>
                    <Size>0</Size>
                    <StorageClass>STANDARD</StorageClass>
                </Contents>
            </ListBucketResult>
        """.strip())).once()

        self.adapter.should_receive('get').with_args(
            'https://s3.amazonaws.com/bucket/',
            auth=self.conn.auth,
            params={'prefix': 'prefix', 'marker': 'prefix/file1'},
        ).and_return(flexmock(raise_for_status=lambda: None, content=b"""
            <?xml version="1.0" encoding="UTF-8"?>
            <ListBucketResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/">
                <Name>bucket</Name>
                <Prefix>prefix</Prefix>
                <Marker>prefix/file1</Marker>
                <MaxKeys>1000</MaxKeys>
                <IsTruncated>false</IsTruncated>
                <Contents>
                    <Key>prefix/file2</Key>
                    <LastModified>2014-06-16T15:58:56.000Z</LastModified>
                    <ETag>&quot;31ed785816f1162fca532cbc80b27266&quot;</ETag>
                    <Size>581708</Size>
                    <StorageClass>STANDARD</StorageClass>
                </Contents>
            </ListBucketResult>
        """.strip())).once()

        self.assertEquals(list(self.r.run()), [{
            'etag': 'd41d8cd98f00b204e9800998ecf8427e',
            'key': 'prefix/file1',
            'last_modified': datetime.datetime(2013, 10, 31, 15, 38, 32),
            'size': 0,
            'storage_class': 'STANDARD',
        }, {
            'etag': '31ed785816f1162fca532cbc80b27266',
            'key': 'prefix/file2',
            'last_modified': datetime.datetime(2014, 6, 16, 15, 58, 56),
            'size': 581708,
            'storage_class': 'STANDARD',
        }])
