# -*- coding: utf-8 -*-

from .connection import Connection
from .pool import Pool
from .multipart_upload import MultipartUpload

# Backward comparability with versions prior to 0.1.7
from .connection import Connection as Conn

__title__ = 'tinys3'
__version__ = '0.1.12'
__author__ = 'Shlomi Atar'
__license__ = 'Apache 2.0'
__all__ = ["Connection", "Conn", "Pool", "MultipartUpload"]
