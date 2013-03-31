from .auth import S3Auth
from .request_factory import RequestFactory
import requests


class Base(object):
    def __init__(self, secret_key, access_key, default_bucket=None):
        """
        Creates a new S3 connection

        :param secret_key:
        :param access_key:
        :param default_bucket:
        """
        self.default_bucket = default_bucket
        self.auth = S3Auth(secret_key, access_key)

    def upload(self, key, local_file,
               bucket=None, expires=None, content_type=None,
               public=True, headers=None):
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
        r = RequestFactory.upload(key, local_file,
                                  bucket=bucket or self.default_bucket,
                                  auth=self.auth,
                                  expires=expires,
                                  content_type=content_type,
                                  public=public,
                                  extra_headers=headers)

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
        to_bucket = to_bucket or self.default_bucket or from_bucket

        r = RequestFactory.copy(from_key, from_bucket,
                                to_key, to_bucket, metadata, public, auth=self.auth)

        return self.run(r)

    def update_metadata(self, key, metadata, bucket=None, public=True):
        """

        :param key:
        :param metadata:
        :param bucket:
        :param public:
        :return:
        """
        bucket = bucket or self.default_bucket

        r = RequestFactory.update_metadata(key, metadata, bucket, public=public, auth=self.auth)

        return self.run(r)

    def delete(self, key, bucket=None):
        """

        :param key:
        :param bucket:
        :return:
        """
        bucket = bucket or self.default_bucket
        r = RequestFactory.delete(key, bucket, auth=self.auth)
        return self.run(r)

    def list(self, bucket=None, marker=None, prefix=None, page_size=1000):
        pass

    def run(self, request):
        """

        :param request:
        :return:
        """
        r = request.prepare()
        return self._handle_request(r)

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
        with requests.Session() as s:
            return s.send(request)