from .request_factory import (UploadPartRequest,
                              InitiateMultipartUploadRequest)


class MultipartUpload:
    """An Amazon S3 multipart upload object to be used in a tinys3 environment.
    Handles data such as:
    - the upload ID (self.uploadId)
    - the bucket (self.bucket)
    - the key (self.key)
    Inspired by the boto implementation."""

    def __init__(self, conn, bucket, key):
        self.conn = conn
        self.bucket = self.conn.bucket(bucket)
        if type(key) is not str:
            self.key = key.encode('utf-8')
        else:
            self.key = key
        self.uploadId = ''

    def initiate(self):
        """A kind of advanced method to send the initiate
        multipart upload POST request. Usually, the user shouldn't call it
        since S3Conn.initiate_multipart_upload does it for you."""
        req = InitiateMultipartUploadRequest(self.conn, self.key, self.bucket)
        self.uploadId = self.conn.run(req)
        return self.uploadId

    def upload_part_from_file(self, fp, part_num, length=None, md5=None,
                              close=False, rewind=True):
        """
        Uploads a part from a file object.

        Params:
        - fp :      the file object
        - part_num: the number of the part (begins from 1 for the first part)
        - length:   (Optional) The size in bytes of the part
        - md5:      (Optional) The base64-encoded 128-bit MD5 digest of the
                    part data. Recommended as a message integrity check to
                    verify that the part data is the same data that was
                    originally sent.

        Returns : The requests response
        """
        extra_headers = {}
        if length is not None:
            extra_headers['Content-Length'] = length
        if md5 is not None:
            extra_headers['Content-MD5'] = md5
        # PUT /ObjectName?partNumber=PartNumber&uploadId=UploadId
        req = UploadPartRequest(self.conn, self.key, self.bucket, fp,
                                part_num, self.uploadId, close, rewind,
                                extra_headers)
        rep = self.conn.run(req)
        return rep

    def complete_upload(self):
        """Method to finish a multipart upload after having uploaded parts.
        This needs to send a POST with each recorded ETag for each part sent by
        the server as response when they were uploaded.
        See http://docs.aws.amazon.com/AmazonS3/latest/API/
        mpUploadComplete.html"""
        from .request_factory import CompleteUploadRequest
        req = CompleteUploadRequest(
            self.conn,
            self.key,
            self.bucket,
            self.uploadId,
            list(self.list_parts())  # Convert the generator to list
        )
        resp = self.conn.run(req)
        return resp

    def cancel_upload(self):
        """Call this method to abort the multipart upload"""
        from .request_factory import CancelUploadRequest
        req = CancelUploadRequest(
            self.conn,
            self.key,
            self.bucket,
            self.uploadId
        )
        return self.conn.run(req)

    def list_parts(self, encoding=None, max_parts=1000, part_number_marker=''):
        """Generator to obtain all uploaded parts of this multipart upload.
        The following extra params can be used:
        - encoding: use 'url' to encode the response.
        - max_parts: Sets the maximum number of parts to return in the response
                     body. Default: 1,000 (Integer)
        - part_number_marker: Specifies the part after which listing should
                              begin. Only parts with higher part numbers will
                              be listed. (String)"""
        from .request_factory import ListPartsRequest
        r = ListPartsRequest(self.conn, self.key, self.bucket, self.uploadId,
                             max_parts, encoding, part_number_marker)
        return self.conn.run(r)

    def number_of_parts(self):
        """Get the number of already uploaded parts.
        Useful when one is interested only in that number, but not the parts
        contents in itself."""
        return len([part for part in self.list_parts()])
