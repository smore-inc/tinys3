from .request_factory import PostRequest, DeleteRequest

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
        self.partsNbr = 0


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

    
    def cancel_upload(self):
        """Call this method to abort the multipart upload"""
        req = DeleteRequest(self.conn, self.key, self.bucket,
                            query_params={'uploadId': self.uploadId})
        return self.conn.run(req)
