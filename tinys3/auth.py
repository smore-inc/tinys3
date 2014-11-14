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

from .util import stringify

# A regexp used for detecting aws bucket names
BUCKET_VHOST_MATCH = re.compile(
    r'^([a-z0-9\-]+\.)?s3([a-z0-9\-]+)?\.amazonaws\.com$',
    flags=re.IGNORECASE)

# A list of query params used by aws
AWS_QUERY_PARAMS = ['versioning', 'location', 'acl', 'torrent', 'lifecycle',
                    'versionid', 'response-content-type',
                    'response-content-language', 'response-expires',
                    'response-cache-control', 'response-content-disposition',
                    'response-content-encoding', 'delete',
                    'uploads', 'partnumber', 'uploadid']


class S3Auth(AuthBase):
    """
    S3 Custom Authenticator class for requests

    This authenticator will sign your requests based on the RESTAuthentication
    specs by Amazon
    http://docs.aws.amazon.com/AmazonS3/latest/dev/RESTAuthentication.html

    You can read more about custom authenticators here:
    http://docs.python-requests.org/en/latest/user/
    advanced.html#custom-authentication

    Usage:

    >>> from tinys3.auth import S3Auth
    >>> requests.put('<S3Url>', data='<S3Data'>, auth=S3Auth('<access_key>',
                                                             '<secret_key>'))
    """

    def __init__(self, access_key, secret_key):
        """
        Initiate the authenticator, using S3 Credentials

        Params:
            - access_key    Your S3 access key
            - secret_key    You S3 secret key

        """
        self.secret_key = secret_key
        self.access_key = access_key

    def sign(self, string_to_sign):
        """
        Generates a signature for the given string

        Params:
            - string_to_sign    The string we want to sign

        Returns:
            Signature in bytes
        """
        string_to_sign = stringify(string_to_sign)
        # Python 3 fix
        if type(string_to_sign) != bytes:
            string_to_sign = string_to_sign.encode('utf8')
        digest = hmac.new(self.secret_key.encode('utf8'),
                          msg=string_to_sign,
                          digestmod=hashlib.sha1).digest()
        return base64.b64encode(digest).strip().decode('ascii')

    def string_to_sign(self, request):
        """
        Generates the string we need to sign on.

        Params:
            - request   The request object

        Returns
            String ready to be signed on

        """

        # We'll use case insensitive dict to store the headers
        h = CaseInsensitiveDict()
        # Add the hearders
        h.update(request.headers)

        # If we have an 'x-amz-date' header,
        # we'll try to use it instead of the date
        if b'x-amz-date' in h or 'x-amz-date' in h:
            date = ''
        else:
            # No x-amz-header, we'll generate a date
            date = h.get('Date') or self._get_date()

        # Set the date header
        request.headers['Date'] = date

        # A fix for the content type header extraction in python 3
        # This have to be done because requests will try to set
        # application/www-url-encoded header if we pass bytes as the content,
        # and the content-type is set with a key that is b'Content-Type' and
        # not 'Content-Type'
        content_type = ''
        if b'Content-Type' in request.headers:
            # Fix content type
            content_type = h.get(b'Content-Type')
            del request.headers[b'Content-Type']
            request.headers['Content-Type'] = content_type

        # The string we're about to generate
        # There's more information about it here:
        # http://docs.aws.amazon.com/AmazonS3/latest/dev/
        # RESTAuthentication.html#ConstructingTheAuthenticationHeader
        msg = [
            # HTTP Method
            request.method,
            # MD5 If provided
            h.get(b'Content-MD5', '') or h.get('Content-MD5', ''),
            # Content type if provided
            content_type or h.get('Content-Type', ''),
            # Date
            date,
            # Canonicalized special amazon headers and resource uri
            self._get_canonicalized_amz_headers(h) +
            self._get_canonicalized_resource(request)
        ]

        # join with a newline and return
        return '\n'.join(msg)

    def _get_canonicalized_amz_headers(self, headers):
        """
        Collect the special Amazon headers, prepare them for signing

        Params:
            - headers   CaseInsensitiveDict with the header requests

        Returns:
            - String with the canonicalized headers

        More information about this process here:
        http://docs.aws.amazon.com/AmazonS3/latest/dev/
        RESTAuthentication.html#
        RESTAuthenticationConstructingCanonicalizedAmzHeaders
        """

        # New dict for the amazon headers
        amz_dict = {}

        # Go over the existing headers
        for k, v in headers.items():
            # Decode the keys if they are encoded
            if isinstance(k, bytes):
                k = k.decode('ascii')

            # to lower case
            k = k.lower()

            # If it starts with 'x-amz' add it to our dict
            if k.startswith('x-amz'):
                amz_dict[k] = v

        result = ""
        # Sort the keys and iterate through them
        for k in sorted(amz_dict.keys()):
            # add stripped key and value to the result string
            result += "{0}:{1}\n".format(k.strip(),
                                         amz_dict[k].strip().replace('\n', ' '))

        # Return the result string
        return result

    def _get_canonicalized_resource(self, request):
        """
        Generates the canonicalized resource string form a request

        You can read more about the process here:
        http://docs.aws.amazon.com/AmazonS3/latest/dev/
        RESTAuthentication.html#ConstructingTheCanonicalizedResourceElement

        Params:
            - request   The request object

        Returns:
            String the canoncicalized resource string.
        """

        r = ""

        # parse our url
        parts = urlparse(request.url)

        # get the host, remove any port identifiers
        host = parts.netloc.split(':')[0]

        if host:
            # try to match our host to
            # <hostname>.s3.amazonaws.com/s3.amazonaws.com
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
        """
        Handle subresources in the query string

        More information about subresources:
        http://docs.aws.amazon.com/AmazonS3/latest/dev/
        RESTAuthentication.html#ConstructingTheCanonicalizedResourceElement
        """
        r = []

        # Split the query string
        # and order the keys lexicographically
        keys = sorted(qs.split('&'))
        # for each item
        for i in keys:
            # get the key
            item = i.split('=')
            k = item[0].lower()
            # If it's one the special params
            if k in AWS_QUERY_PARAMS:
                # add it to our result list
                r.append(i)
        # If we have result, convert them to query string
        if r:
            return '?' + '&'.join(r)
        return ''

    def _get_date(self):
        """
        Returns a string for the current date
        """
        return datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')

    def _fix_content_length(self, request):
        """
        Amazon requires to have content-length header when using the put
        request, however, requests won't add this header, so we need to add it
        ourselves.

        Params:
            - request   The request object
        """

        if request.method == 'PUT' and 'Content-Length' not in request.headers:
            request.headers['Content-Length'] = '0'

    def __call__(self, r):
        """
        The entry point of the custom authenticator.

        When used as an auth class, requests will call this method just before
        sending the request.

        Params:
            - r     The request object

        Returns:
            The request object, after we've updated some headers
        """

        # Generate the string to sign
        msg = self.string_to_sign(r)
        # Sign the string and add the authorization header
        r.headers['Authorization'] = "AWS {0}:{1}".format(
            self.access_key, self.sign(msg))

        # Fix an issue with 0 length requests
        self._fix_content_length(r)

        # return the request
        return r
