from datetime import timedelta
import mimetypes
from requests import Request


class RequestFactory(object):
    @classmethod
    def bucket_url(cls, key, bucket, ssl=False):
        protocol = 'https' if ssl else 'http'

        return "%s://s3.amazonaws.com/%s/%s" % (protocol, bucket, key.lstrip('/'))

    @classmethod
    def upload(cls, key, local_file, auth,
               bucket, expires=None, content_type=None,
               public=True, extra_headers=None):
        # get the url
        url = cls.bucket_url(key, bucket)

        # set the content type
        content_type = content_type or mimetypes.guess_type(key)[0] or 'application/octet-stream'

        # Handle content expiration
        if expires == 'max':
            expires = timedelta(seconds=31536000)
        elif isinstance(expires, int):
            expires = timedelta(seconds=expires)
        else:
            expires = expires

        # set headers
        headers = {'Content-Type': content_type}

        if public:
            headers['x-amz-acl'] = 'public-read'

        if expires:
            headers['Cache-Control'] = "max-age=%d" % expires.total_seconds() + ', public' if public else ''

        # update headers with the extras
        if extra_headers:
            headers.update(extra_headers)

        return Request(method='put', url=url, headers=headers, auth=auth, data=local_file)

    @classmethod
    def copy(cls, from_key, from_bucket, to_key, to_bucket, metadata, public, auth):
        from_key = from_key.lstrip('/')
        to_key = to_key.lstrip('/')

        headers = {
            'x-amz-copy-source': "/%s/%s" % (from_bucket, from_key),
            'x-amz-metadata-directive': 'COPY' if not metadata else 'REPLACE'
        }

        if public:
            headers['x-amz-acl'] = 'public-read'

        if metadata:
            headers.update(metadata)

        return Request(method='put',
                       url=cls.bucket_url(to_key, to_bucket),
                       headers=headers, auth=auth)


    @classmethod
    def update_metadata(cls, key, metadata, bucket, public, auth):
        return cls.copy(key, bucket, key, bucket, metadata, public, auth)

    @classmethod
    def delete(cls, key, bucket, auth):
        url = cls.bucket_url(key, bucket)

        return Request(method='DELETE', url=url, auth=auth)

    @classmethod
    def list(cls, bucket=None, marker=None, prefix=None, page_size=1000):
        pass