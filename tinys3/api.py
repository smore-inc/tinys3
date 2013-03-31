"""
tinys3.api
~~~~~~~~~~~~

This module implements the tinys3 API.

"""

from . import Conn


def _conn(auth):
    return Conn(auth[0], auth[1])


def upload(auth, key, local_file, bucket,
           expires=None, content_type=None, public=True, headers=None):
    """


    :param key:
    :param local_file:
    :param bucket:
    :param auth:
    :param expires:
    :param content_type:
    :param public:
    :param headers:
    """

    return _conn(auth).upload(key, local_file, bucket, expires, content_type, public, headers)


def copy(auth, from_key, from_bucket, to_key, to_bucket=None, metadata=None, public=True):
    """

    :param auth:
    :param from_key:
    :param from_bucket:
    :param to_key:
    :param to_bucket:
    :param metadata:
    :param public:
    """

    return _conn(auth).copy(from_key, from_bucket, to_key, to_bucket, metadata, public)


def update_metadata(auth, key, metadata, bucket, public=True):
    """

    :param auth:
    :param key:
    :param metadata:
    :param bucket:
    :param public:
    """

    return _conn(auth).update_metadata(key, metadata, bucket, public)


def delete(auth, key, bucket):
    return _conn(auth).delete(key, bucket)


def list():
    pass