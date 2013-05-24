# -*- coding: utf-8 -*-

from requests.auth import AuthBase
from requests.structures import CaseInsensitiveDict
from datetime import datetime
import hashlib
import hmac
import base64
import re



# Python 2/3 support
try:
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse

BUCKET_VHOST_MATCH = re.compile(r'^([a-z0-9\-]+\.)?s3\.amazonaws\.com$', flags=re.IGNORECASE)

AWS_QUERY_PARAMS = ['versioning', 'location', 'acl', 'torrent', 'lifecycle', 'versionid',
                    'response-content-type', 'response-content-language', 'response-expires', 'response-cache-control',
                    'response-content-disposition', 'response-content-encoding', 'delete']


class S3Auth(AuthBase):
    """
    Authenticate S3 requests
    """

    def __init__(self, access_key, secret_key):
        """

        """
        self.secret_key = secret_key
        self.access_key = access_key

    def sign(self, string_to_sign):
        digest = hmac.new(self.secret_key.encode('utf8'),
                          msg=string_to_sign.encode('utf8'),
                          digestmod=hashlib.sha1).digest()

        return base64.b64encode(digest).strip().decode('ascii')

    def string_to_sign(self, request):
        h = CaseInsensitiveDict()
        h.update(request.headers)

        # Try to use

        if b'x-amz-date' in h or 'x-amz-date' in h:
            date = ''
        else:
            date = h.get('Date') or self._get_date()
            request.headers['Date'] = date

        # Set the date header
        request.headers['Date'] = date

        # A fix for the content type header extraction in python 3
        # This have to be done because requests will try to set application/www-url-encoded herader
        # if we pass bytes as the content, and the content-type is set with a key that is b'Content-Type' and not
        # 'Content-Type'
        content_type = ''
        if b'Content-Type' in request.headers:
            # Fix content type
            content_type = h.get(b'Content-Type')
            del request.headers[b'Content-Type']
            request.headers['Content-Type'] = content_type

        msg = [
            request.method,
            h.get(b'Content-MD5', '') or h.get('Content-MD5', ''),
            content_type or h.get('Content-Type', ''),
            date,
            self._get_canonicalized_amz_headers(h) + self._get_canonicalized_resource(request)
        ]

        return '\n'.join(msg)

    def _get_canonicalized_amz_headers(self, headers):
        """
        Collect the special Amazon headers, prepare them for signing
        """

        amz_dict = {}

        for k, v in headers.items():
            if isinstance(k, bytes):
                k = k.decode('ascii')

            k = k.lower()

            if k.startswith('x-amz'):
                amz_dict[k] = v

        result = ""
        for k in sorted(amz_dict.keys()):
            result += "%s:%s\n" % (k.strip(), amz_dict[k].strip().replace('\n', ' '))

        return result

    def _get_canonicalized_resource(self, request):

        r = ""

        # parse our url
        parts = urlparse(request.url)

        # get the host, remove any port identifiers
        host = parts.netloc.split(':')[0]

        if host:
            # try to match our host to <hostname>.s3.amazonaws.com/s3.amazonaws.com
            m = BUCKET_VHOST_MATCH.match(host)
            if m:
                bucket = (m.groups()[0] or '').rstrip('.')

                if bucket:
                    r += ('/' + bucket)
            else:
                # It's a virtual host, add it to the result
                r += ('/' + host)

        # Add the path string
        r += parts.path or '/'

        # add the special query strings
        r += self._get_subresource(parts.query)

        return r

    def _get_subresource(self, qs):
        r = []

        keys = qs.split('&')
        for i in keys:
            item = i.split('=')
            k = item[0].lower()

            if k in AWS_QUERY_PARAMS:
                r.append(i)

        if r:
            return '?' + '&'.join(r)

        return ''

    def _get_date(self):
        return datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')

    def __call__(self, r):
        msg = self.string_to_sign(r)
        r.headers['Authorization'] = "AWS %s:%s" % (self.access_key, self.sign(msg))
        return r