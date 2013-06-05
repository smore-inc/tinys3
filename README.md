tinys3 - Quick and minimal S3 uploads for Python
================================================

[![Build Status](https://travis-ci.org/smore-inc/tinys3.png?branch=master)](https://travis-ci.org/smore-inc/tinys3)

A simple Python S3 upload library.
Inspired by one of my favorite packages, [requests](http://docs.python-requests.org/en/latest/).

tinys3 is used at [Smore](https://www.smore.com) to upload more than 1.5 million keys to S3 every month.

Usage example:

```python
import tinys3

conn = tinys3.Connection(S3_ACCESS_KEY,S3_SECRET_KEY,ssl=True)

f = open('some_file.zip','rb')
conn.upload('some_file.zip',f,'my_bucket')

```


Features
--------

* Upload files to S3
* Copy keys inside/between buckets
* Delete keys
* Update key metadata
* Simple way to set key as public and setting Cache-Control and Content-Type
* Pool implementation for fast multi-threaded actions


Support
-------
* Python 2.6
* Python 2.7
* Python 3.2
* Python 3.3
* PyPy


Installation
------------

```
$ pip install tinys3
```

Or if you're using easy_install:

```
$ easy_install tinys3
```

Usage
=====


Uploading files to S3
---------------------

Uploading a single file:

```python
import tinys3

# Creating a simple connection
conn = tinys3.Connection(S3_ACCESS_KEY,S3_SECRET_KEY)

# Uploading a single file
f = open('some_file.zip','rb')
conn.upload('some_file.zip',f,'my_bucket')

```

Some more options for the connection:

```python

# Specifying a default bucket
conn = tinys3.Connection(S3_ACCESS_KEY,S3_SECRET_KEY,default='my_bucket')

# So we could skip the bucket parameter on every request

f = open('some_file.zip','rb')
conn.upload('some_file.zip',f)

# Controlling the use of ssl
conn = tinys3.Connection(S3_ACCESS_KEY,S3_SECRET_KEY,ssl=True)
```

Setting expiry headers.

```python

# File will be stored in cache for one hour
conn.upload('my_awesome_key.zip',f,bucket='sample_bucket',
            expires=3600)

# Passing 'max' as the value to 'expires' will make it cachable for a year
conn.upload('my_awesome_key.zip',f,bucket='sample_bucket',
            expires='max')

# Expires can also handle timedelta object
from datetime import timedelta

t = timedelta(weeks=5)
# File will be stored in cache for 5 weeks
conn.upload('my_awesome_key.zip',f,bucket='sample_bucket',
            expires=t)
```

tinys3 will try to guess the content type from the key (using the mimetypes package),
but you can override it

```python
conn.upload('my_awesome_key.zip',f,bucket='sample_bucket',
            content_type='application/zip')
```

Setting additional headers is also possible by passing a dict to the headers argument:

```python
conn.upload('my_awesome_key.zip',f,bucket='sample_bucket',
            headers={
            'x-amz-storage-class': 'REDUCED_REDUNDANCY'
            })
```

For more information, see [Amazon's S3 Documentation](http://docs.aws.amazon.com/AmazonS3/latest/API/RESTObjectPUT.html
)


Copy keys inside/between buckets
--------------------------------


Use the 'copy' method to copy a key or update metadata.

```python
# Simple copy between two buckets
conn.copy('source_key.jpg','source_bucket','target_key.jpg','target_bucket')

# No need to specify the target bucket if we're copying inside the same bucket
conn.copy('source_key.jpg','source_bucket','target_key.jpg')

# We could also update the metadata of the target file
conn.copy('source_key.jpg','source_bucket','target_key.jpg','target_bucket',
            metadata={ 'x-amz-storage-class': 'REDUCED_REDUNDANCY'})

# Or set the target file as private
conn.copy('source_key.jpg','source_bucket','target_key.jpg','target_bucket',
            public=False)

```

Updating metadata
-------------

```python

# Updating metadata for a key
conn.update_metadata('key.jpg',{ 'x-amz-storage-class': 'REDUCED_REDUNDANCY'},'my_bucket')

# We can also change the privacy of a file, without updating it's metadata
conn.update_metadata('key.jpg',{},'my_bucket',public=False)

```

Deleting keys
-------------

```python

# Deleting keys is simple
conn.delete('key.jpg','my_bucket')

```

Using tinys3's Connection Pool
-------------------

Creating a pool:

```python
pool = tinys3.Pool(S3_ACCESS_KEY,S3_SECRET_KEY)
```

The pool can use the same parameters as Connection:
```python
pool = tinys3.Pool(S3_ACCESS_KEY,S3_SECRET_KEY,ssl=True, default_bucket='my_bucket')
```

The pool uses 5 worker threads by default. The 'size' parameter allows us to override it:
```python
pool = tinys3.Pool(S3_ACCESS_KEY,S3_SECRET_KEY,size=25)
```

Using the pool to perform actions:

```python
# Let's use the pool to delete a file
>>> r = pool.delete('a_key_to_delete.zip','my_bucket')
<Future at 0x2c8de48L state=pending>

# Futures are the standard python implementation of the "promise" pattern.
# You can read more about them here:
# http://docs.python.org/3.3/library/concurrent.futures.html#future-objects

# Did we finish?
>>> r.done()
False

# Block until the response is completed
>>> r.result()
<Response [200]>

# Block until completed with a timeout.
# If the response is not completed until the timeout has passed, a TimeoutError will be raised
>>> r.result(timeout=120)
<Response [200]>

```

Using as_completed and all_completed:

```python
# First we'll create a lot of async requests
>>> requests = []
>>> for i in range(100)
>>>     requests.append(pool.delete('key' + str(i), 'my_bucket'))

# The helper methods as_completed and all_completed helps us work
# with multiple Future objects.

# This will block until all the requests are completed
# The results are the responses themselves, without the Future wrappers
>>> pool.all_completed(requests)
[<Response [200]>, ... ]

# The as_completed generator will yield on every completed request:
>>> for r in pool.as_completed(requests)
>>>     # r is the response object itself, without the Future wrapper
>>>     print r
```

