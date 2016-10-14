# -*- coding: utf-8 -*-

"""

tinys3.request_factory
~~~~~~~~~~~~~~~~~~~~~~

Generates Request objects for various S3 requests

"""

import datetime
import mimetypes
import os
import requests
# Python 2/3 compatibility
try:
    from urllib import quote
except ImportError:
    from urllib.parse import quote

from .util import LenWrapperStream, stringify

# A fix for windows pc issues with mimetypes
# http://grokbase.com/t/python/python-list/129tb1ygws/
# mimetypes-guess-type-broken-in-windows-on-py2-7-and-python-3-x
mimetypes.init([])

XML_PARSE_STRING = "{{http://s3.amazonaws.com/doc/2006-03-01/}}{0}"


class S3Request(object):
    def __init__(self, conn, params=None):
        self.auth = conn.auth
        self.tls = conn.tls
        self.endpoint = conn.endpoint
        self.params = params

    def bucket_url(self, key, bucket):
        """Function to generate the request URL. Is used by every request"""
        protocol = 'https' if self.tls else 'http'
        key = stringify(key)
        bucket = stringify(bucket)
        url = "{0}://{1}.{2}/{3}".format(protocol, bucket, self.endpoint,
                                         key.lstrip('/'))
        # If params have been specified, add them to URL in the format :
        # url?param1&param2=value, etc.
        if self.params is not None:
            first = True
            # Sort params so they are processed alphabetically
            # to ensure that the generated URL is always the same, to avoid
            # sometimes making tests checking the input URL fail.
            for (param, value) in sorted(self.params.items()):
                if first is True:
                    url += "?"
                    first = False
                else:
                    url += "&"
                url += param
                # Some parameters (e.g. subresource descriptors) have no value
                if value is not None:
                    url += "={0}".format(value)
        return url

    def run(self):
        raise NotImplementedError()

    def adapter(self):
        """
        Returns the adapter to use when issuing a request.
        useful for testing
        """
        return requests


class GetRequest(S3Request):
    def __init__(self, conn, key, bucket, headers=None):
        super(GetRequest, self).__init__(conn)
        self.key = key
        self.bucket = bucket
        self.headers = headers

    def run(self):
        url = self.bucket_url(self.key, self.bucket)
        r = self.adapter().get(url, auth=self.auth, headers=self.headers)
        r.raise_for_status()
        return r


class ListRequest(S3Request):
    def __init__(self, conn, prefix, bucket):
        super(ListRequest, self).__init__(conn)
        if prefix and type(prefix) is not str:
            prefix = prefix.encode('utf-8')
        self.prefix = prefix
        self.bucket = bucket

    def run(self):
        return iter(self)

    def __iter__(self):
        marker = ''
        more = True
        url = self.bucket_url('', self.bucket)
        k = XML_PARSE_STRING.format

        try:
            import lxml.etree as ET
        except ImportError:
            import xml.etree.ElementTree as ET

        while more:
            resp = self.adapter().get(url, auth=self.auth, params={
                'prefix': self.prefix,
                'marker': marker,
            })
            resp.raise_for_status()
            root = ET.fromstring(resp.content)
            for tag in root.findall(k('Contents')):
                p = {
                    'key': tag.find(k('Key')).text,
                    'size': int(tag.find(k('Size')).text),
                    'last_modified': datetime.datetime.strptime(
                        tag.find(k('LastModified')).text,
                        '%Y-%m-%dT%H:%M:%S.%fZ',
                    ),
                    'etag': tag.find(k('ETag')).text[1:-1],
                    'storage_class': tag.find(k('StorageClass')).text,
                }
                yield p
            more = root.find(k('IsTruncated')).text == 'true'
            if more:
                marker = p['key']


class ListMultipartUploadRequest(S3Request):
    def __init__(self, conn, prefix, bucket, max_uploads, encoding, key_marker,
                 upload_id_marker):
        params = {'uploads': None}
        super(ListMultipartUploadRequest, self).__init__(conn, params)
        self.conn = conn
        if type(prefix) is not str:
            self.prefix = prefix.encode('utf-8')
        else:
            self.prefix = prefix
        self.bucket = bucket
        self.max_uploads = max_uploads
        self.encoding = encoding

        self.key_marker = key_marker
        self.upload_id_marker = upload_id_marker

    def run(self):
        return iter(self)

    def __iter__(self):
        more = True
        url = self.bucket_url('', self.bucket)
        k = XML_PARSE_STRING.format

        try:
            import lxml.etree as ET
        except ImportError:
            import xml.etree.ElementTree as ET
        from .multipart_upload import MultipartUpload

        while more:
            resp = self.adapter().get(url, auth=self.auth, params={
                'encoding-type': self.encoding,
                'max-uploads': self.max_uploads,
                'key-marker': self.key_marker,
                'prefix': self.prefix,
                'upload-id-marker': self.upload_id_marker
            })
            resp.raise_for_status()
            root = ET.fromstring(resp.content)
            for tag in root.findall(k('Upload')):
                mp = MultipartUpload(self.conn, self.bucket,
                                     tag.find(k('Key')).text)
                mp.uploadId = tag.find(k('UploadId')).text
                yield mp

            more = root.find(k('IsTruncated')).text == 'true'
            if more:
                self.key_marker = root.find(k('NextKeyMarker')).text
                self.upload_id_marker = root.find(k('NextUploadIdMarker')).text


class ListPartsRequest(S3Request):
    def __init__(self, conn, key, bucket, upload_id, max_parts,
                 encoding, part_number_marker):
        params = {'uploadId': upload_id}
        super(ListPartsRequest, self).__init__(conn, params)
        self.key = key
        self.bucket = bucket
        self.encoding = encoding
        self.upload_id = upload_id
        self.max_parts = max_parts
        self.part_number_marker = part_number_marker

    def run(self):
        return iter(self)

    def __iter__(self):
        more = True
        url = self.bucket_url(self.key, self.bucket)
        k = XML_PARSE_STRING.format

        try:
            import lxml.etree as ET
        except ImportError:
            import xml.etree.ElementTree as ET
        while more:
            resp = self.adapter().get(url, auth=self.auth, params={
                'encoding-type': self.encoding,
                'max-parts': self.max_parts,
                'part-number-marker': self.part_number_marker
            })
            resp.raise_for_status()
            root = ET.fromstring(resp.content)
            for tag in root.findall(k('Part')):
                part = {
                    'part_number': int(tag.find(k('PartNumber')).text),
                    'last_modified': tag.find(k('LastModified')).text,
                    'etag': tag.find(k('ETag')).text,
                    'size': int(tag.find(k('Size')).text)
                }
                yield part

            more = root.find(k('IsTruncated')).text == 'true'
            if more:
                self.part_number_marker = root.find(
                    k('NextPartNumberMarker')).text


class InitiateMultipartUploadRequest(S3Request):
    def __init__(self, conn, key, bucket):
        params = {'uploads': None}
        super(InitiateMultipartUploadRequest, self).__init__(conn, params)
        self.key = key
        self.bucket = bucket

    def run(self, data=None):
        url = self.bucket_url(self.key, self.bucket)
        k = XML_PARSE_STRING.format
        try:
            import lxml.etree as ET
        except ImportError:
            import xml.etree.ElementTree as ET
        r = self.adapter().post(url, auth=self.auth)
        r.raise_for_status()
        root = ET.fromstring(r.content)
        return root.find(k('UploadId')).text


class DeleteRequest(S3Request):
    def __init__(self, conn, key, bucket):
        super(DeleteRequest, self).__init__(conn)
        self.key = key
        self.bucket = bucket

    def run(self):
        url = self.bucket_url(self.key, self.bucket)
        r = self.adapter().delete(url, auth=self.auth)
        r.raise_for_status()
        return r


class HeadRequest(S3Request):
    def __init__(self, conn, bucket, key='', headers=None):
        super(HeadRequest, self).__init__(conn)
        self.key = key
        self.bucket = bucket
        self.headers = headers

    def run(self):
        url = self.bucket_url(self.key, self.bucket)
        r = self.adapter().head(url, auth=self.auth, headers=self.headers)
        r.raise_for_status()
        return r


class UploadRequest(S3Request):
    def __init__(self, conn, key, local_file, bucket, expires=None,
                 content_type=None, public=True, extra_headers=None,
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
        if self.expires is not None:
            headers['Cache-Control'] = self._calc_cache_control()
        # calc the content type
        if self.content_type is not None:
            headers['Content-Type'] = self.content_type
        elif mimetypes.guess_type(self.key)[0] is not None:
            headers['Content-Type'] = mimetypes.guess_type(self.key)[0]
        else:
            headers['Content-Type'] = 'application/octet-stream'
        # if public - set public headers
        if self.public:
            headers['x-amz-acl'] = 'public-read'
        # if rewind - rewind the fp like object
        if self.rewind and hasattr(self.fp, 'seek'):
            self.fp.seek(0, os.SEEK_SET)
        # update headers with extra headers
        if self.extra_headers:
            headers.update(self.extra_headers)
        try:
            # Wrap our file pointer with a LenWrapperStream.
            # We do it because requests will try to fallback to chunked
            # transfer if it can't extract the len attribute of the object it
            # gets, and S3 doesn't support chunked transfer.
            # In some cases, like cStreamIO, it may cause some issues, so we
            # wrap the stream with a class of our own, that will proxy the
            # stream and provide a proper len attribute
            # TODO - add some tests for that
            # shlomiatar @ 08/04/13
            data = LenWrapperStream(self.fp)
            # call requests with all the params
            r = self.adapter().put(self.bucket_url(self.key, self.bucket),
                                   data=data,
                                   headers=headers,
                                   auth=self.auth)
            r.raise_for_status()
        finally:
            # if close is set, try to close the fp like object
            # (also, use finally to ensure the close)
            if self.close and hasattr(self.fp, 'close'):
                self.fp.close()
        return r

    def _calc_cache_control(self):
        expires = self.expires
        # Handle content expiration
        if expires == 'max':
            expires = datetime.timedelta(seconds=31536000)
        elif isinstance(expires, int):
            expires = datetime.timedelta(seconds=expires)
        else:
            expires = expires
        max_age = "max-age={0}".format(self._get_total_seconds(expires))
        max_age += ', public' if self.public else ''
        return max_age

    def _get_total_seconds(self, timedelta):
        """
        Support for getting the total seconds from a time delta
        (Required for python 2.6 support)
        """
        return timedelta.days * 24 * 60 * 60 + timedelta.seconds


class UploadPartRequest(S3Request):

    def __init__(self, conn, key, bucket, fp, part_num,
                 upload_id, close, rewind, headers=None):
        params = {'partNumber': part_num, 'uploadId': upload_id}
        super(UploadPartRequest, self).__init__(conn, params)
        self.key = key
        self.bucket = bucket
        self.fp = fp
        self.headers = headers
        self.close = close
        self.rewind = rewind

    def run(self):
        # if rewind - rewind the fp like object
        if self.rewind and hasattr(self.fp, 'seek'):
            self.fp.seek(0, os.SEEK_SET)
        try:
            data = self.fp
            # call requests with all the params
            r = self.adapter().put(self.bucket_url(self.key, self.bucket),
                                   data=data,
                                   headers=self.headers,
                                   auth=self.auth)
            r.raise_for_status()
        finally:
            # if close is set, try to close the fp like object
            # (also, use finally to ensure the close)
            if self.close and hasattr(self.fp, 'close'):
                self.fp.close()
        return r


class CompleteUploadRequest(S3Request):

    def __init__(self, conn, key, bucket, uploadId, parts_list):
        params = {'uploadId': uploadId}
        super(CompleteUploadRequest, self).__init__(conn, params)
        self.key = key
        self.bucket = bucket
        self.parts_list = parts_list

    def run(self):
        # We need to pass some HTML in the POST request data body.
        # It includes all the ETags headers sent by the server responses when
        # parts were uploaded, in order
        data = "<CompleteMultipartUpload>"
        for part in self.parts_list:
            data += "<Part>"
            data += "<PartNumber>{0}</PartNumber>".format(part['part_number'])
            data += "<ETag>{0}</ETag>".format(part['etag'])
            data += "</Part>"
        data += "</CompleteMultipartUpload>"
        # POST /ObjectName?uploadId=UploadId
        url = self.bucket_url(self.key, self.bucket)
        r = self.adapter().post(url, auth=self.auth, data=data)
        r.raise_for_status()
        return r


class CancelUploadRequest(S3Request):

    def __init__(self, conn, key, bucket, uploadId):
        params = {'uploadId': uploadId}
        super(CancelUploadRequest, self).__init__(conn, params)
        self.key = key
        self.bucket = bucket

    def run(self):
        # DELETE /ObjectName?uploadId=UploadId
        url = self.bucket_url(self.key, self.bucket)
        r = self.adapter().delete(url, auth=self.auth)
        r.raise_for_status()
        return r


class CopyRequest(S3Request):

    def __init__(self, conn, from_key, from_bucket, to_key, to_bucket,
                 metadata=None, public=True):
        super(CopyRequest, self).__init__(conn)
        # stringify + quote combo is to correctly manage Unicode filenames
        # (they must be encoded like within an URL)
        self.from_key = quote(stringify(from_key.lstrip('/')))
        self.from_bucket = stringify(from_bucket)
        # Not 'quoting' the destination key since the url encode is done later
        self.to_key = stringify(to_key.lstrip('/'))
        self.to_bucket = stringify(to_bucket)
        self.metadata = metadata
        self.public = public

    def run(self):
        headers = {
            'x-amz-copy-source': "/%s/%s" % (self.from_bucket,
                                             self.from_key)
        }
        if not self.metadata:
            headers['x-amz-metadata-directive'] = 'COPY'
        else:
            headers['x-amz-metadata-directive'] = 'REPLACE'
        if self.public:
            headers['x-amz-acl'] = 'public-read'
        if self.metadata:
            headers.update(self.metadata)
        r = self.adapter().put(self.bucket_url(self.to_key, self.to_bucket),
                               auth=self.auth, headers=headers)
        r.raise_for_status()
        return r


class UpdateMetadataRequest(CopyRequest):
    def __init__(self, conn, key, bucket, metadata=None, public=True):
        super(UpdateMetadataRequest, self).__init__(conn, key, bucket, key,
                                                    bucket, metadata=metadata,
                                                    public=public)
