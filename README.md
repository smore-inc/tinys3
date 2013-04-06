tinys3
======

[![Build Status](https://travis-ci.org/smore-inc/tinys3.png?branch=master)](https://travis-ci.org/smore-inc/tinys3)

A simple python S3 upload library. Inspired by requests

Usage example:

```python

import tinys3

conn = tinys3.Conn(S3_SECRET_KEY,S3_ACCESS_KEY)

with open('some_file.zip','rb') as f:
    conn.upload('some_file.zip',f,'my_bucket', expires='max')

```


Features
--------

* Upload files to S3
* Copy keys inside/between buckets
* Delete keys
* Update key's metadata
* Simple way to set expires headers, content type, content publicity
* Pool implementation for fast multi-threaded actions
* Bucket content iterator


Support
-------
* Python 2.6
* Python 2.7
* Python 3.2

Installation
------------

```
$ pip install tinys3
```