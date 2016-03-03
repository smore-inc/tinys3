import unittest
from flexmock import flexmock
# Support for python 2/3
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO
from tinys3 import Connection
from tinys3.request_factory import (
    InitiateMultipartUploadRequest, UploadPartRequest, CompleteUploadRequest,
    CancelUploadRequest, ListMultipartUploadRequest, ListPartsRequest
)


class TestMultipartUpload(unittest.TestCase):
    def setUp(self):
        """
        Create a default connection
        """
        self.conn = Connection("TEST_ACCESS_KEY", "TEST_SECRET_KEY", tls=True)
        # Some test values we use among the unit tests...
        self.test_key = 'test_key'
        self.test_bucket = 'bucket'
        self.uploadId = ("VXBsb2FkIElEIGZvciA2aWWpbmcncyBteS1tb3ZpZS5t"
                         "MnRzIHVwbG9hZA")

    def _mock_adapter(self, request):
        """
        Creates a mock object and replace the result of the adapter method
        """
        mock_obj = flexmock()
        flexmock(request).should_receive('adapter').and_return(mock_obj)

        return mock_obj

    def test_multipart_upload_initiate_request(self):
        """Test the request to initiate a multipart upload"""
        req = InitiateMultipartUploadRequest(
            self.conn, self.test_key, self.test_bucket
        )
        mock = self._mock_adapter(req)
        # Taken from
        # http://docs.aws.amazon.com/AmazonS3/latest/API/mpUploadInitiate.html#mpUploadInitiate-examples
        response_content = """<?xml version="1.0" encoding="UTF-8"?>
        <InitiateMultipartUploadResult
        xmlns="http://s3.amazonaws.com/doc/2006-03-01/">
          <Bucket>{0}</Bucket>
          <Key>{1}</Key>
          <UploadId>{2}</UploadId>
        </InitiateMultipartUploadResult>
        """.format(self.test_bucket, self.test_key, self.uploadId)

        mock.should_receive('post').with_args(
            'https://{0}.s3.amazonaws.com/{1}?uploads'.format(
                self.test_bucket, self.test_key),
            auth=self.conn.auth
        ).and_return(flexmock(
            raise_for_status=lambda: None,
            content=response_content)
        ).once()

        response_upload_id = req.run()
        self.assertEquals(response_upload_id, self.uploadId)

    def test_upload_part_from_file_request(self):
        """Test the request to upload a part to a multipart upload"""
        s = StringIO("dummy")
        part_nbr = 1
        req = UploadPartRequest(
            self.conn,
            self.test_key,
            self.test_bucket,
            s,
            part_nbr,
            self.uploadId,
            False,
            False
        )
        mock = self._mock_adapter(req)
        # In python3 uploadId and partNumber are reversed in order...
        # But both URLs are valid
        mock.should_receive("put").with_args(
            'https://{0}.s3.amazonaws.com/{1}?partNumber={2}&uploadId={3}'
            .format(
                self.test_bucket, self.test_key, part_nbr, self.uploadId),
            headers=None,
            data=s,
            auth=self.conn.auth
        ).and_return(flexmock(raise_for_status=lambda: None)).once()

        req.run()

    def test_complete_multipart_upload(self):
        """Test the request to complete a multipart upload"""
        parts_list = [{'part_number': 1,
                       'last_modified': '2016-02-29T19:48:33.000Z',
                       'etag': "79b281060d337b9b2b84ccf390adcf74",
                       'size': 5242880},
                      {'part_number': 2,
                       'last_modified': '2016-02-29T19:49:17.000Z',
                       'etag': "0cc175b9c0f1b6a831c399e269772661",
                       'size': 1}]

        data = "<CompleteMultipartUpload>"
        for part in parts_list:
            data += "<Part>"
            data += "<PartNumber>{0}</PartNumber>".format(part['part_number'])
            data += "<ETag>{0}</ETag>".format(part['etag'])
            data += "</Part>"
        data += "</CompleteMultipartUpload>"
        req = CompleteUploadRequest(
            self.conn,
            self.test_key,
            self.test_bucket,
            self.uploadId,
            parts_list
        )
        mock = self._mock_adapter(req)
        mock.should_receive('post').with_args(
            'https://{0}.s3.amazonaws.com/{1}?uploadId={2}'.format(
                self.test_bucket, self.test_key, self.uploadId),
            auth=self.conn.auth,
            data=data
        ).and_return(flexmock(raise_for_status=lambda: None)).once()

        req.run()

    def test_cancel_multipart_upload(self):
        """Test the request to cancel a multipart upload"""
        req = CancelUploadRequest(
            self.conn,
            self.test_key,
            self.test_bucket,
            self.uploadId
        )
        mock = self._mock_adapter(req)
        mock.should_receive('delete').with_args(
            'https://{0}.s3.amazonaws.com/{1}?uploadId={2}'.format(
                self.test_bucket, self.test_key, self.uploadId),
            auth=self.conn.auth
        ).and_return(flexmock(raise_for_status=lambda: None)).once()

        req.run()

    def test_list_multipart_uploads(self):
        """Test the request to list active multipart uploads"""
        # Taken from
        # http://docs.aws.amazon.com/AmazonS3/latest/API/mpUploadListMPUpload.html
        response_content = """<?xml version="1.0" encoding="UTF-8"?>
        <ListMultipartUploadsResult
        xmlns="http://s3.amazonaws.com/doc/2006-03-01/">
            <Bucket>{0}</Bucket>
            <KeyMarker></KeyMarker>
            <UploadIdMarker></UploadIdMarker>
            <NextKeyMarker>my-movie.m2ts</NextKeyMarker>
            <NextUploadIdMarker>YW55IGlkZWEgd2h5IGVsdmluZydzIHVwbG9hZCBmYWlsZWQ
            </NextUploadIdMarker>
            <MaxUploads>1000</MaxUploads>
            <IsTruncated>false</IsTruncated>
            <Upload>
                <Key>{1}</Key>
                <UploadId>{2}</UploadId>
                <Initiator>
                    <ID>arn:aws:iam::111122223333:user/user1-11111a31-17b5-4fb7-9df5-b111111f13de</ID>
                    <DisplayName>user1-11111a31-17b5-4fb7-9df5-b111111f13de</DisplayName>
                </Initiator>
                <Owner>
                    <ID>75aa57f09aa0c8caeab4f8c24e99d10f8e7faeebf76c078efc7c6caea54ba06a</ID>
                    <DisplayName>OwnerDisplayName</DisplayName>
                </Owner>
                <StorageClass>STANDARD</StorageClass>
                <Initiated>2010-11-10T20:48:33.000Z</Initiated>
            </Upload>
        </ListMultipartUploadsResult>
        """.format(self.test_bucket, self.test_key, self.uploadId)

        my_params = {'encoding-type': None,
                     'max-uploads': 1000,
                     'key-marker': '',
                     'prefix': '',
                     'upload-id-marker': ''}
        req = ListMultipartUploadRequest(
            self.conn,
            my_params['prefix'],
            self.test_bucket,
            my_params['max-uploads'],
            my_params['encoding-type'],
            my_params['key-marker'],
            my_params['upload-id-marker']
        )
        mock = self._mock_adapter(req)
        mock.should_receive('get').with_args(
            'https://{0}.s3.amazonaws.com/?uploads'.format(
                self.test_bucket, self.test_key),
            auth=self.conn.auth,
            params=my_params
        ).and_return(flexmock(
            raise_for_status=lambda: None,
            content=response_content)).once()

        mp_uploads = list(req.run())
        self.assertEqual(len(mp_uploads), 1)
        self.assertEqual(mp_uploads[0].key, self.test_key)
        self.assertEqual(mp_uploads[0].bucket, self.test_bucket)
        self.assertEqual(mp_uploads[0].uploadId, self.uploadId)

    def test_list_parts_request(self):
        """Test the request to list the parts of a multipart upload"""
        # Taken from
        # http://docs.aws.amazon.com/AmazonS3/latest/API/mpUploadListParts.html
        response_content = """<?xml version="1.0" encoding="UTF-8"?>
        <ListPartsResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/">
            <Bucket>{0}</Bucket>
            <Key>{1}</Key>
            <UploadId>{2}</UploadId>
            <Initiator>
                    <ID>arn:aws:iam::111122223333:user/some-user-11116a31-17b5-4fb7-9df5-b288870f11xx</ID>
                    <DisplayName>umat-user-11116a31-17b5-4fb7-9df5-b288870f11xx</DisplayName>
                </Initiator>
                <Owner>
                    <ID>75aa57f09aa0c8caeab4f8c24e99d10f8e7faeebf76c078efc7c6caea54ba06a</ID>
                    <DisplayName>someName</DisplayName>
                </Owner>
                <StorageClass>STANDARD</StorageClass>
                <PartNumberMarker>1</PartNumberMarker>
                <NextPartNumberMarker>3</NextPartNumberMarker>
                <MaxParts>2</MaxParts>
                <IsTruncated>false</IsTruncated>
            <Part>
                <PartNumber>1</PartNumber>
                <LastModified>2010-11-10T20:48:34.000Z</LastModified>
                <ETag>"7778aef83f66abc1fa1e8477f296d394"</ETag>
                <Size>10485760</Size>
            </Part>
            <Part>
                <PartNumber>2</PartNumber>
                <LastModified>2010-11-10T20:48:33.000Z</LastModified>
                <ETag>"aaaa18db4cc2f85cedef654fccc4a4x8"</ETag>
                <Size>10485760</Size>
            </Part>
        </ListPartsResult>
        """.format(self.test_bucket, self.test_key, self.uploadId)
        my_params = {'encoding-type': None,
                     'max-parts': 3,
                     'part-number-marker': ''}
        req = ListPartsRequest(
            self.conn,
            self.test_key,
            self.test_bucket,
            self.uploadId,
            my_params['max-parts'],
            my_params['encoding-type'],
            my_params['part-number-marker']
        )

        mock = self._mock_adapter(req)
        mock.should_receive('get').with_args(
            'https://{0}.s3.amazonaws.com/{1}?uploadId={2}'.format(
                self.test_bucket, self.test_key, self.uploadId),
            auth=self.conn.auth,
            params=my_params
            ).and_return(flexmock(
                raise_for_status=lambda: None,
                content=response_content)).once()

        parts = list(req.run())
        self.assertEqual(len(parts), 2)
        for (partIdx, part) in enumerate(parts):
            self.assertEqual(part['part_number'], partIdx + 1)
        self.assertEqual(parts[0]['last_modified'], "2010-11-10T20:48:34.000Z")
        self.assertEqual(parts[0]['etag'],
                         '"7778aef83f66abc1fa1e8477f296d394"')
        self.assertEqual(parts[0]['size'], 10485760)
        self.assertEqual(parts[1]['last_modified'], "2010-11-10T20:48:33.000Z")
        self.assertEqual(parts[1]['etag'],
                                 '"aaaa18db4cc2f85cedef654fccc4a4x8"')
        self.assertEqual(parts[1]['size'], 10485760)
