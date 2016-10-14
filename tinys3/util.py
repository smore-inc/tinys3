import os


def stringify(s):
    """In Py3k, unicode are strings, so we mustn't encode it.
    However it is necessary in Python 2.x, since Unicode strings are
    unicode, not str."""
    if type(s) != str and type(s) != bytes:
        s = s.encode('utf-8')
    return s


class LenWrapperStream(object):
    """
    A simple class to wrap a stream and provide length capability
    for streams like cStringIO

     We do it because requests will try to fallback to chuncked transfer if
     it can't extract the len attribute of the object it gets, and S3 doesn't
     support chuncked transfer.
     In some cases, like cStringIO, it may cause some issues, so we wrap the
     stream with a class of our own, that will proxy the stream and provide a
     proper len attribute
    """

    def __init__(self, stream):
        """
        Creates a new wrapper from the given stream

        Params:
            - stream    The baseline stream

        """
        self.stream = stream

    def read(self, n=-1):
        """
        Proxy for reading the stream
        """
        return self.stream.read(n)

    def __iter__(self):
        """
        Proxy for iterating the stream
        """
        return self.stream

    def seek(self, pos, mode=0):
        """
        Proxy for the `seek` method of the underlying stream
        """
        return self.stream.seek(pos, mode)

    def tell(self):
        """
        Proxy for the `tell` method of the underlying stream
        """
        return self.stream.tell()

    def __len__(self):
        """
        Calculate the stream length in a fail-safe way
        """
        o = self.stream

        # If we have a '__len__' method
        if hasattr(o, '__len__'):
            return len(o)

        # If we have a len property
        if hasattr(o, 'len'):
            return o.len

        # If we have a fileno property
        # (EAFP here, because some file-like objs like
        # tarfile "ExFileObject" will pass a hasattr test
        # but still not work)
        try:
            return os.fstat(o.fileno()).st_size
        except (IOError, AttributeError):
            # fallback to the manual way,
            # this is useful when using something like BytesIO
            pass


        # calculate based on bytes to end of content
        # get our start position
        start_pos = o.tell()
        # move to the end
        o.seek(0, os.SEEK_END)
        # Our len is end - start position
        size = o.tell() - start_pos
        # Seek the stream back to the start position
        o.seek(start_pos)
        # Return the size
        return size

    def __eq__(self, other):
        """
        Make sure equal method works as expected (comparing the underlying
        stream and not the wrapper)
        """
        if self.stream == other:
            return True

        if isinstance(other, LenWrapperStream) and other.stream == self.stream:
            return True

    @property
    def closed(self):
        """
        Proxy for the underlying stream closed property
        """
        return self.stream.closed

    def __repr__(self):
        """
        Proxy for the repr of the stream
        """
        return repr(self.stream)
