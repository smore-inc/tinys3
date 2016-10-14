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

    files = ["""
        <Contents>
            <Key>prefix/file1</Key>
            <LastModified>2013-10-31T15:38:32.000Z</LastModified>
            <ETag>&quot;d41d8cd98f00b204e9800998ecf8427e&quot;</ETag>
            <Size>0</Size>
            <StorageClass>STANDARD</StorageClass>
        </Contents>
    """, """
        <Contents>
            <Key>prefix/file2</Key>
            <LastModified>2014-06-16T15:58:56.000Z</LastModified>
            <ETag>&quot;31ed785816f1162fca532cbc80b27266&quot;</ETag>
            <Size>581708</Size>
            <StorageClass>STANDARD</StorageClass>
        </Contents>
    """]

    parsed_files = [{
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
    }]

    def setup_adapter(self, marker, files, truncated):
        self.adapter.should_receive('get').with_args(
            'https://bucket.s3.amazonaws.com/',
            # 'https://s3.amazonaws.com/bucket/',
            auth=self.conn.auth,
            params={'prefix': 'prefix', 'marker': marker},
        ).and_return(flexmock(
            raise_for_status=lambda: None,
            content="""
                <?xml version="1.0" encoding="UTF-8"?>
                <ListBucketResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/">
                    <Name>bucket</Name>
                    <Prefix>prefix</Prefix>
                    <Marker>{0}</Marker>
                    <MaxKeys>1000</MaxKeys>
                    <IsTruncated>{1}</IsTruncated>
                    {2}
                </ListBucketResult>
            """.format(
                marker,
                'true' if truncated else 'false',
                files,
            ).strip().encode('utf-8'),
        )).once()

    def test_simple_list_request(self):
        """
        Test the generation of a list request
        """
        self.setup_adapter('', '\n'.join(self.files), False)
        self.assertEquals(list(self.r.run()), self.parsed_files)

    def test_chained_list_requests(self):
        """
        Test the generation of a more complex list request
        """

        self.setup_adapter('', self.files[0], True)
        self.setup_adapter('prefix/file1', self.files[1], False)

        self.assertEquals(list(self.r.run()), self.parsed_files)
