class Key:
    """A S3 key. Just a data handler class for now.
    Main attributes:
    - lastmodified: timestamp of last modification
    - etag: The entity tag is an MD5 hash of the object.
    - storageclass: Amazon S3 storage class
                    (STANDARD | REDUCED_REDUNDANCY | GLACIER)
    - key: Key name
    - size: size in bytes
    """
    def __init__(self, bucket, data_dict):
        self.bucket = bucket
        for key in data_dict:
            setattr(self, key, data_dict[key])
