import collections  # For OrderedDict
from .request_factory import GetRequest, PostRequest, DeleteRequest, UploadPartRequest

class MultipartUpload:
    """An Amazon S3 multipart upload object to be used in an tinys3 environment.
    Handles data such as:
    - the upload ID
    - the concerned bucket/key
    - a parts number indicating how much parts we already sent on that upload
    It uses a custom basic HTTP parser in order to retrieve the upload ID from
    the HTTP response upon initialization.
    Inspired by the boto implementation."""        

    def __init__(self, conn, bucket, key):
        self.conn = conn
        self.bucket = self.conn.bucket(bucket)
        self.key = key
        self.uploadId = ''
        self.partsNbr = 1  # Amazon s3 parts numbers begin from 1.
        # we need to keep track of the returned etag for each uploaded part as
        # we need to send them to the server when completing the upload.
        # See http://docs.aws.amazon.com/AmazonS3/latest/API/
        # mpUploadComplete.html
        self.etags = {}


    def initiate(self):
        """A kind of advanced method to send the initiate
        multipart upload POST request. Usually, the user shouldn't call it
        since S3Conn.initiate_multipart_upload does it for you."""
        req = PostRequest(self.conn, self.key, self.bucket,
                          query_params={"uploads": None})
        resp = self.conn.run(req)
        parser = self.conn.UploadIdParser()
        parser.feed(resp.text)
        self.uploadId = parser.upload_id()


    def complete_upload(self):
        """Method to finish a multipart upload after having uploaded parts.
        This needs to send a POST with each recorded ETag for each part sent by
        the server as response when they were uploaded."""
        # We need to pass some HTML in the POST request data body.
        # It includes all the ETags headers sent by the server responses when
        # parts were uploaded
        # we need parts in order so use an OrderedDict
        parts = collections.OrderedDict(sorted(self.etags.items()))
        data = "<CompleteMultipartUpload>"
        for (partNumber, etag) in parts.items():
            data += "<Part>"
            data += "<PartNumber>{}</PartNumber>".format(partNumber)
            data += "<ETag>{}</ETag>".format(etag)
            data += "</Part>"
        data += "</CompleteMultipartUpload>"
        req = PostRequest(self.conn, self.key, self.bucket,
                          query_params={"uploadId": self.uploadId}, data=data)
        resp = self.conn.run(req)
        return resp


    def cancel_upload(self):
        """Call this method to abort the multipart upload"""
        req = DeleteRequest(self.conn, self.key, self.bucket,
                            query_params={'uploadId': self.uploadId})
        return self.conn.run(req)


    def upload_part_from_file(self, fp, headers=None):
        """
        The available headers for this request are :
        - Content-Length: The size of the part, in bytes.
        - Content-MD5: The base64-encoded 128-bit MD5 digest of the part data.
          Recommended as a message integrity check to verify that the part data
          is the same data that was originally sent.
        - Expect: When your application uses 100-continue, it does not send the
          request body until it receives an acknowledgment.
        See http://docs.aws.amazon.com/AmazonS3/latest/API/
            mpUploadUploadPart.html
        """
        req = UploadPartRequest(self.conn, self.key, self.bucket, fp,
                            extra_headers=headers,
                            query_params={'partNumber': self.partsNbr,
                                          'uploadId': self.uploadId})
        rep = self.conn.run(req)
        self.etags[self.partsNbr] = rep.headers['etag']
        self.partsNbr += 1
        return rep


    def list_parts(self, extra_params=None):
        """The following extra params can be used to list parts:
        - encoding-type: use 'url' to encode the response.
        - max-parts: Sets the maximum number of parts to return in the response
                     body. Default: 1,000
        - part-number-marker: Specifies the part after which listing should
                              begin. Only parts with higher part numbers will
                              be listed."""

        params = {"uploadId": self.uploadId}
        if extra_params is not None:
            params.update(extra_params)
        more_parts = True
        while more_parts:
            # GET /ObjectName?uploadId=UploadId&params
            req = GetRequest(self.conn, self.key, self.bucket,
                             query_params=params)
            resp = self.conn.run(req)
            parser = self.conn.UploadIdParser()
            parser.feed(resp.text)
            for part in parser.parts:
                yield Part(part)
            if parser.data['istruncated'] == 'true':
                params['part-number-marker'] = parser.data['nextpartnumbermarker']
            else:
                more_parts = False


class Part:
    """A part of a multipart upload.
    Attributes:
    - partnumber - The integer part number
    - lastmodified - The last modified date of this part
    - etag - The MD5 hash of this part
    - size - The size, in bytes, of this part
    """
    def __init__(self, data_dict):
        for key in data_dict:
            setattr(self, key, data_dict[key])
