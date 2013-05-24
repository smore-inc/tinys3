# -*- coding: utf-8 -*-

from .auth import S3Auth
from .request_factory import UploadRequest, UpdateMetadataRequest, CopyRequest, DeleteRequest


class Base(object):
    def __init__(self, access_key, secret_key, default_bucket=None, ssl=False):
        """
        Creates a new S3 connection

        :param access_key:
        :param secret_key:
        :param default_bucket:
        """
        self.default_bucket = default_bucket
        self.auth = S3Auth(access_key, secret_key)
        self.ssl = ssl

    def bucket(self, bucket):
        b = bucket or self.default_bucket

        if not b:
            raise ValueError("You must specify a bucket in your request or set the default_bucket for the connection")

        return b

    def upload(self, key, local_file,
               bucket=None, expires=None, content_type=None,
               public=True, headers=None, rewind=True, close=False):
        """

        :param key:
        :param local_file:
        :param bucket:
        :param expires:
        :param content_type:
        :param public:
        :param headers:
        :return:
        """
        r = UploadRequest(self, key, local_file, self.bucket(bucket), expires=expires, content_type=content_type,
                          public=public, extra_headers=headers, rewind=rewind, close=close)

        return self.run(r)

    def copy(self, from_key, from_bucket, to_key, to_bucket=None, metadata=None, public=True):
        """

        :param from_key:
        :param from_bucket:
        :param to_key:
        :param to_bucket:
        :param metadata:
        :param public:
        :return:
        """
        to_bucket = self.bucket(to_bucket or from_bucket)

        r = CopyRequest(self, from_key, from_bucket, to_key, to_bucket, metadata=metadata, public=public)

        return self.run(r)

    def update_metadata(self, key, metadata, bucket=None, public=True):
        """

        :param key:
        :param metadata:
        :param bucket:
        :param public:
        :return:
        """
        r = UpdateMetadataRequest(self, key, self.bucket(bucket), metadata, public)

        return self.run(r)

    def delete(self, key, bucket=None):
        """

        :param key:
        :param bucket:
        :return:
        """
        r = DeleteRequest(self, key, self.bucket(bucket))

        return self.run(r)

    def list(self, bucket=None, marker=None, prefix=None, page_size=1000):
        pass

    def run(self, request):
        """

        :param request:
        :return:
        """
        return self._handle_request(request)

    def _handle_request(self, request):
        """

        :param request:
        :raise:
        """
        raise NotImplementedError


class Conn(Base):
    """

    """

    def _handle_request(self, request):
        """

        :param request:
        :return:
        """
        return request.run()