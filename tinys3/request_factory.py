# -*- coding: utf-8 -*-

"""

tinys3.request_factory
~~~~~~~~~~~~~~~~~~~~~~

Generates Request objects for various S3 requests

"""

from datetime import timedelta
import mimetypes
import os
import requests

# A fix for windows pc issues with mimetypes
# http://grokbase.com/t/python/python-list/129tb1ygws/mimetypes-guess-type-broken-in-windows-on-py2-7-and-python-3-x
from .util import LenWrapperStream

mimetypes.init([])


class S3Request(object):
    def __init__(self, conn):
        self.auth = conn.auth
        self.ssl = conn.ssl

    def bucket_url(self, key, bucket):
        protocol = 'https' if self.ssl else 'http'

        return "%s://s3.amazonaws.com/%s/%s" % (protocol, bucket, key.lstrip('/'))

    def run(self):
        raise NotImplementedError()


class UploadRequest(S3Request):
    def __init__(self, conn, key, local_file, bucket, expires=None, content_type=None, public=True, extra_headers=None,
                 close=False, rewind=True):
        """



        :param conn:
        :param key:
        :param local_file:
        :param bucket:
        :param expires:
        :param content_type:
        :param public:
        :param extra_headers:
        :param close:
        :param rewind:
        """
        super(UploadRequest, self).__init__(conn)

        self.key = key
        self.fp = local_file
        self.bucket = bucket
        self.expires = expires
        self.content_type = content_type
        self.public = public
        self.extra_headers = extra_headers
        self.close = close
        self.rewind = rewind

    def run(self):

        headers = {}

        # calc the expires headers
        if self.expires:
            headers['Cache-Control'] = self._calc_cache_control()

        # calc the content type
        headers['Content-Type'] = self.content_type or mimetypes.guess_type(self.key)[0] or 'application/octet-stream'

        # if public - set public headers
        if self.public:
            headers['x-amz-acl'] = 'public-read'

        # if content is string, use it to open a fp
        if isinstance(self.fp, basestring):
            self.fp = open(self.fp, 'rb')
            # make sure we close the fp when we finish
            self.close = True

        # if rewind - rewind the fp like object
        if self.rewind:
            self.fp.seek(0, os.SEEK_SET)

        # update headers with extra headers
        if self.extra_headers:
            headers.update(self.extra_headers)

        try:
            # Wrap our file pointer with a LenWrapperStream.
            # We do it because requests will try to fallback to chuncked transfer if
            # it can't extract the len attribute of the object it gets, and S3 doesn't
            # support chuncked transfer.
            # In some cases, like cStreamIO, it may cause some issues, so we wrap the stream
            # with a class of our own, that will proxy the stream and provide a proper
            # len attribute
            #
            # TODO - add some tests for that
            # shlomiatar @ 08/04/13
            data = LenWrapperStream(self.fp)

            # call requests with all the params
            r = requests.put(self.bucket_url(self.key, self.bucket),
                             data=data,
                             headers=headers,
                             auth=self.auth)

        finally:
            # if close is set, try to close the fp like object (also, use finally to ensure the close)
            if self.close:
                self.fp.close()

        return r

    def _calc_cache_control(self):

        expires = self.expires
        # Handle content expiration
        if expires == 'max':
            expires = timedelta(seconds=31536000)
        elif isinstance(expires, int):
            expires = timedelta(seconds=expires)
        else:
            expires = expires

        return "max-age=%d" % self._get_total_seconds(expires) + ', public' if self.public else ''

    def _get_total_seconds(self, timedelta):
        """
        Support for getting the total seconds from a time delta (Required for python 2.6 support)
        """
        return timedelta.days * 24 * 60 * 60 + timedelta.seconds


class DeleteRequest(S3Request):
    def __init__(self, conn, key, bucket):
        super(DeleteRequest, self).__init__(conn)
        self.key = key
        self.bucket = bucket

    def run(self):
        url = self.bucket_url(self.key, self.bucket)
        return requests.delete(url, auth=self.auth)


class CopyRequest(S3Request):
    def __init__(self, conn, from_key, from_bucket, to_key, to_bucket, metadata=None, public=True):
        super(CopyRequest, self).__init__(conn)
        self.from_key = from_key.lstrip('/')
        self.from_bucket = from_bucket
        self.to_key = to_key.lstrip('/')
        self.to_bucket = to_bucket
        self.metadata = metadata
        self.public = public

    def run(self):

        headers = {
            'x-amz-copy-source': "/%s/%s" % (self.from_bucket, self.from_key),
            'x-amz-metadata-directive': 'COPY' if not self.metadata else 'REPLACE'
        }

        if self.public:
            headers['x-amz-acl'] = 'public-read'

        if self.metadata:
            headers.update(self.metadata)

        return requests.put(self.bucket_url(self.to_key, self.to_bucket), auth=self.auth, headers=headers)


class UpdateMetadataRequest(CopyRequest):
    def __init__(self, conn, key, bucket, metadata=None, public=True):
        super(UpdateMetadataRequest, self).__init__(conn, key, bucket, key, bucket, metadata=metadata, public=public)
