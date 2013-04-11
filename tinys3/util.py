import os


class LenWrapperStream(object):
    """
    A simple class to wrap a stream and provide length capability
    for streams like cStringIO

     We do it because requests will try to fallback to chuncked transfer if
     it can't extract the len attribute of the object it gets, and S3 doesn't
    # support chuncked transfer.
    # In some cases, like cStreamIO, it may cause some issues, so we wrap the stream
    # with a class of our own, that will proxy the stream and provide a proper
    # len attribute
    """

    def __init__(self, stream):
        self.stream = stream

    def read(self, n=-1):
        return self.stream.read(n)

    def __iter__(self):
        return self.stream

    def seek(self, pos, mode=0):
        return self.stream.seek(pos, mode)

    def tell(self):
        return self.stream.tell()

    def __len__(self):
        o = self.stream
        if hasattr(o, '__len__'):
            return len(o)
        if hasattr(o, 'len'):
            return o.len
        if hasattr(o, 'fileno'):
            return os.fstat(o.fileno()).st_size

        # calculate based on bytes to end of content
        spos = o.tell()
        o.seek(0, os.SEEK_END)
        size = o.tell() - spos
        o.seek(spos)
        return size

    def __eq__(self, other):
        if self.stream == other:
            return True

        if isinstance(other, LenWrapperStream) and other.stream == self.stream:
            return True

    @property
    def closed(self):
        return self.stream.closed


    def __repr__(self):
        return repr(self.stream)