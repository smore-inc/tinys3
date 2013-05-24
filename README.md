tinys3
======

[![Build Status](https://travis-ci.org/smore-inc/tinys3.png?branch=master)](https://travis-ci.org/smore-inc/tinys3)

A simple python S3 upload library. Inspired by requests

Usage example:

```python
import tinys3

conn = tinys3.Conn(S3_ACCESS_KEY,S3_SECRET_KEY,ssl=True)

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
* Bucket keys iterator


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


Usage
=====


Uploading files to S3
---------------------

Uploading a simple file:

```python
import tinys3

# Creating a simple connection
conn = tinys3.Conn(S3_ACCESS_KEY,S3_SECRET_KEY)

# Uploading a single file
with open('some_file.zip','rb') as f:
    conn.upload('some_file.zip',f,'my_bucket')
```

Some more options for the connection:

```python

# Specifying a default bucket
conn = tinys3.Conn(S3_ACCESS_KEY,S3_SECRET_KEY,default='my_bucket')

# So we could skip the bucket parameter on every request

with open('some_file.zip','rb') as f:
    conn.upload('some_file.zip',f)

# Controlling the use of ssl
conn = tinys3.Conn(S3_ACCESS_KEY,S3_SECRET_KEY,ssl=True)
```

Setting expiry headers

```python

# File will be stored in cache for one hour:
conn.upload('my_awesome_key.zip','my_local_file.zip',bucket='sample_bucket',
            expires=3600)

# Passing 'max' as the value to 'expires' will make it cachable for a year
conn.upload('my_awesome_key.zip','my_local_file.zip',bucket='sample_bucket',
            expires='max')

# Expires can also handle timedelta object:
from datetime import timedelta

t = timedelta(weeks=5)
# File will be stored in cache for 5 weeks
conn.upload('my_awesome_key.zip','my_local_file.zip',bucket='sample_bucket',
            expires=t)
```

tinys3 will try to guess the content type from the key, but you can override it:

```python
conn.upload('my_awesome_key.zip','my_local_file.zip',bucket='sample_bucket',
            content_type='application/zip')
```

Setting additional headers is also possible by passing a dict to the headers kwarg:

```python
conn.upload('my_awesome_key.zip','my_local_file.zip',bucket='sample_bucket',
            headers={
            'x-amz-storage-class': 'REDUCED_REDUNDANCY'
            })
```

For more information on headers you can use:
http://docs.aws.amazon.com/AmazonS3/latest/API/RESTObjectPUT.html


Copy keys inside/between buckets
--------------------------------


Use the 'copy' method to copy a key or update metadata

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

Deleting keys
-------------

```python

# Updating metadata for a key
conn.update_metadata('key.jpg',{ 'x-amz-storage-class': 'REDUCED_REDUNDANCY'},'my_bucket')

# We can also change the privacy of a file, without updating it's metadata
conn.update_metadata('key.jpg',{},'my_bucket',public=False)

```

Using tinys3's Pool
-------------------

Creating a pool:

```python
pool = tinys3.Conn(S3_ACCESS_KEY,S3_SECRET_KEY)
```

The pool can use the same parameters as Conn:
```python
pool = tinys3.Conn(S3_ACCESS_KEY,S3_SECRET_KEY,ssl=True, default_bucket='my_bucket')
```

The pool is using 5 worker threads by default. The param 'size' allows us to override it:
```python
pool = tinys3.Conn(S3_ACCESS_KEY,S3_SECRET_KEY,size=25)
```

Using the pool to perform actions:

```python
# Let's use the pool to delete a file
r = pool.delete('a_key_to_delete.zip','my_bucket')
>>> <AsyncResponse completed=False>

# The AsyncResponse is a wrapper to allow us to work with the async nature of the pool

# is completed?
r.completed()
>>> False

# Block until the response is completed
r.response()
>>> <Response [200]>

# Block until completed with a timeout.
# if the response is not completed until the timeout has passed, a TimeoutError will be raised
r.response(timeout=120)
>>> <Response [200]>

```

Using as_completed and all_completed:

```python
# First we'll create a lot of async requests
requests = [pool.delete('key%s' % i, 'my_bucket') for i in range(100)]

# The helper methods as_completed and all_completed helps us work
# with multiple AsyncResponse objects.

# This will block until all the requests are completed
# The results are the responses themselves, without the AsyncResponse wrappers
pool.all_completed(requests)
>>> [<Response [200]>, ... ]


# The as_completed generator will yield on every completed request:
for r in pool.as_completed(requests)
    # r is the response object itself, without the AsyncResponse wrapper
    print r
```

