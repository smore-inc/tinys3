# -*- coding: utf-8 -*-

from .auth import S3Auth
from .request_factory import (UploadRequest, UpdateMetadataRequest,
                              CopyRequest, DeleteRequest, GetRequest,
                              ListRequest, ListMultipartUploadRequest,
                              HeadRequest)


class Base(object):
    """
    The "Base" connection object, Handles the common S3 tasks
    (upload, copy, delete,etc)

    This is an "abstract" class, both Connection and Pool implement it.
    """

    def __init__(self, access_key, secret_key, default_bucket=None, tls=False,
                 endpoint="s3.amazonaws.com"):
        """
        Creates a new S3 connection

        Params:
            - access_key        AWS access key
            - secret_key        AWS secret key
            - default_bucket    (Optional) Sets the default bucket, so requests
              inside this pool won't have to specify
                                the bucket every time.
            - tls               (Optional) Make the requests using secure
              connection (Defaults to False)
            - endpoint          (Optional) Sets the s3 endpoint.

        """
        self.default_bucket = default_bucket
        self.auth = S3Auth(access_key, secret_key)
        self.tls = tls
        self.endpoint = endpoint

    def bucket(self, bucket):
        """
        Verifies that we have a bucket for a request

        Params:
            - bucket    The name of the bucket we're trying to use, None if we
              want to use the default bucket

        Returns:
            The bucket to use for the request

        Raises:
            ValueError if no bucket was provided AND no default bucket was
            defined.
        """
        if bucket and type(bucket) is not str:
            bucket = bucket.encode('utf-8')
        b = bucket or self.default_bucket
        # If we don't have a bucket, raise an exception
        if not b:
            raise ValueError("You must specify a bucket in your request or set"
                             "the default_bucket for the connection")
        return b

    def get(self, key, bucket=None, headers=None):
        """
        Get a key from a bucket

        Params:
            - key           The key to get

            - bucket        (Optional) The name of the bucket to use
            (can be skipped if setting the default_bucket)
            - headers       (Optional) Additional headers of the request

        Returns:
            - A response object from the requests lib or a future that wraps
            that response object if used with a pool.

        Usage:

        >>> conn.get('my_awesome_key.zip','sample_bucket')

        """
        r = GetRequest(self, key, self.bucket(bucket), headers=headers)
        return self.run(r)

    def list(self, prefix='', bucket=None):
        """
        List files

        Params:
            - prefix        (Optional) List only files starting with this prefix (default to the empty string)

            - bucket        (Optional) The name of the bucket to use (can be skipped if setting the default_bucket option) for the connection

        Returns:
            - An iterator over the files, each file being represented by a dict object with the following keys:
                - etag
                - key
                - last_modified
                - size
                - storage_class


        Usage:

        >>> conn.list('rep/','sample_bucket')

        """
        r = ListRequest(self, prefix, self.bucket(bucket))

        return self.run(r)

    def upload(self, key, local_file,
               bucket=None, expires=None, content_type=None,
               public=True, headers=None, rewind=True, close=False):
        """
        Upload a file and store it under a key

        Params:
            - key           The key to store the file under.

            - local_file    A file-like object which would be uploaded

            - bucket        (Optional) The name of the bucket to use (can be
              skipped if setting the default_bucket)
                            option for the connection

            - expires       (Optional) Sets the the Cache-Control headers. The
              value can be a number (used as seconds),
                            A Timedelta or the 'max' string, which will
                            automatically set the file to be cached for a
                            year. Defaults to no caching

            - content_type  (Optional) Explicitly sets the Content-Type header.
              if not specified, tinys3 will try to guess the right content type
              for the file (using the mimetypes lib)

            - public        (Optional) If set to true, tinys3 will set the file
              to be publicly available using the acl headers. Defaults to True.

            - headers       (Optional) Allows you to specify extra headers for
              the request using a dict.

            - rewind        (Optional) If true, tinys3 will seek the file like
              object to the beginning before uploading. Defaults to True.

            - Close         (Optional) If true, tinys3 will close the file like
              object after the upload was complete

        Returns:
            - A response object from the requests lib or a future that wraps
              that response object if used with a pool.

        Usage:

        >>> with open('my_local_file.zip', 'rb') as f:
        >>>     conn.upload('my_awesome_key.zip',f,
        >>>                 expires='max',
        >>>                 bucket='sample_bucket',
        >>>                 headers={
        >>>                     'x-amz-storage-class': 'REDUCED_REDUNDANCY'
        >>>                 })

        There are more usage examples in the readme file.

        """
        r = UploadRequest(self, key, local_file, self.bucket(bucket),
                          expires=expires, content_type=content_type,
                          public=public, extra_headers=headers, rewind=rewind,
                          close=close)
        return self.run(r)

    def copy(self, from_key, from_bucket, to_key, to_bucket=None,
             metadata=None, public=True):
        """
        Copy a key contents to another key/bucket with an option to update
        metadata/public state

        Params:
            - from_key      The source key
            - from_bucket   The source bucket
            - to_key        The target key
            - to_bucket     (Optional) The target bucket, if not specified,
              tinys3 will use the `from_bucket`
            - metadata      (Optional) Allows an override of the new key's
              metadata. if not defined, tinys3 will copy the source key's
              metadata.
            - public        (Optional) Same as upload, should the new key be
              publicly accessible? Default to True.

        Returns:
            - A response object from the requests lib or a future that wraps
              that response object if used with a pool.

        Usage:
            >>> conn.copy('source_key.jpg','source_bucket','target_key.jpg',
                          'target_bucket',
                       metadata={ 'x-amz-storage-class': 'REDUCED_REDUNDANCY'})

        There are more usage examples in the readme file.
        """
        to_bucket = self.bucket(to_bucket or from_bucket)
        r = CopyRequest(self, from_key, from_bucket, to_key, to_bucket,
                        metadata=metadata, public=public)
        return self.run(r)

    def update_metadata(self, key, metadata=None, bucket=None, public=True):
        """
        Updates the metadata information for a file

        Params:
            - key           The key to update
            - metadata      (Optional) The metadata dict to set for the key
            - public        (Optional) Same as upload, should the key be
              publicly accessible? Default to True.

        Returns:
            - A response object from the requests lib or a future that wraps
              that response object if used with a pool.

        Usage:
            >>> conn.update_metadata('key.jpg',
                {'x-amz-storage-class': 'REDUCED_REDUNDANCY'},'my_bucket')

        There are more usage examples in the readme file.
        """
        r = UpdateMetadataRequest(self, key, self.bucket(bucket), metadata,
                                  public)

        return self.run(r)

    def delete(self, key, bucket=None):
        """
        Delete a key from a bucket

        Params:
            - key           The key to delete

            - bucket        (Optional) The name of the bucket to use (can be
              skipped if setting the default_bucket) for the connection

        Returns:
            - A response object from the requests lib or a future that wraps
              that response object if used with a pool.

        Usage:

        >>> conn.delete('my_awesome_key.zip','sample_bucket')

        """
        r = DeleteRequest(self, key, self.bucket(bucket))
        return self.run(r)

    def run(self, request):
        """
        Executes an S3Request and returns the result

        Params:
            - request An instance of S3Request

        """
        return self._handle_request(request)

    def head_bucket(self, bucket=None):
        r = HeadRequest(self, self.bucket(bucket))
        return self.run(r)

    def head_object(self, key, bucket=None, headers=None):
        r = HeadRequest(self, self.bucket(bucket), key)
        return self.run(r)

    def list_multipart_uploads(self, prefix='', bucket=None, encoding=None,
                               max_uploads=1000, key_marker='',
                               upload_id_marker=''):
        """
        List a bucket's ongoing multipart uploads

        Params:
            - prefix            (Optional) List only files starting with this
                                prefix (default to the empty string)

            - bucket            (Optional) The name of the bucket to use (can
                                be skipped if setting the default_bucket
                                option) for the connection

            - encoding:         (Optional) You can encode the response with
                                'url' (default to the empty string)

            - max-uploads:      (Optional) Sets the maximum number of returned
                                uploads in the response (default to 1000)

            - key-marker:       (Optional) Together with upload-id-marker, this
                                parameter specifies the multipart upload after
                                which listing should begin. (default to the
                                empty string)

            - upload_id_marker: (Optional) Together with key-marker, specifies
                                the multipart upload after which listing should
                                begin. (default to the empty string)

        Returns:
            - An iterator over the files, each file being represented by a dict
              object with the following keys:
                - etag
                - key
                - last_modified
                - size
                - storage_class


        Usage:

        >>> conn.list_multipart_uploads('rep/','sample_bucket')

        """
        r = ListMultipartUploadRequest(self, prefix, self.bucket(bucket),
                                       max_uploads, encoding, key_marker,
                                       upload_id_marker)

        return self.run(r)

    def get_all_multipart_uploads(self, bucket=None, prefix=''):
        """The non-generator version of list_multipart_uploads."""
        mps = [mp for mp in self.list_multipart_uploads(prefix, bucket)]
        return mps

    def initiate_multipart_upload(self, key, bucket=None):
        """Returns a "boto-ish" MultipartUpload object that works kind of
        the same way than the Boto one."""
        from .multipart_upload import MultipartUpload

        mp = MultipartUpload(self, bucket, key)
        mp.initiate()
        return mp

    def _handle_request(self, request):
        """
        An abstract method, to be implemented by inheriting classes
        """
        raise NotImplementedError


class Connection(Base):
    """
    The basic implementation of an S3 connection.
    """

    def _handle_request(self, request):
        """
        Implements S3Request execution.

        Params:
            - request       S3Request object to run

        """
        return request.run()
