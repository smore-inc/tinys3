from HTMLParser import HTMLParser
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

    class UploadIdParser(HTMLParser):
        """An internal HTML parser to parse server responses.
        This shouldn't be of any use outside of the class."""
        
        def __init__(self):
            HTMLParser.__init__(self)
            self.data = {}
            self.currentTag = None


        def handle_starttag(self, tag, attrs):
            self.currentTag = tag


        def handle_endtag(self, tag):
            self.currentTag = None


        def handle_data(self, data):
            try:
                # Stored tag names are all lowercase
                self.data[self.currentTag] = data
            except KeyError:
                # As Amazon answers XML, the parser calls an empty handle_data
                # before 'real' HTML parsing. But nothing to worry about.
                pass

            
        def upload_id(self):
            return self.data['uploadid']

        
        def key(self):
            return self.data['key']

        
        def bucket(self):
            return self.data['bucket']
        

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
        parser = self.UploadIdParser()
        parser.feed(resp.text)
        self.uploadId = parser.upload_id()

    
    def cancel_upload(self):
        """Call this method to abort the multipart upload"""
        req = DeleteRequest(self.conn, self.key, self.bucket,
                            query_params={'uploadId': self.uploadId})
        return self.conn.run(req)
