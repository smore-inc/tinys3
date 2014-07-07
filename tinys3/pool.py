# -*- coding: utf-8 -*
from .connection import Base

from concurrent.futures import ThreadPoolExecutor, as_completed
from concurrent.futures import wait


class Pool(Base):
    def __init__(self, access_key, secret_key, default_bucket=None, tls=False,
                 endpoint="s3.amazonaws.com", size=5):
        """
        Create a new pool.

        Params:
            - access_key        AWS access key
            - secret_key        AWS secret key
            - default_bucket    (Optional) Sets the default bucket, so requests
              inside this pool won't have to specify
                                the bucket every time.
            - tls               (Optional) Make the requests using secure
              connection (Defaults to False)
            - endpoint          (Optional) Sets the s3 endpoint.
            - size              (Optional) The maximum number of worker threads
              to use (Defaults to 5)

        Notes:
            - The pool uses the concurrent.futures library to implement the
              worker threads.
            - You can use the pool as a context manager, and it will close
              itself (and it's workers) upon exit.
        """

        # Call to the base constructor
        super(Pool, self).__init__(access_key, secret_key, tls=tls,
                                   default_bucket=default_bucket,
                                   endpoint=endpoint)

        # Setup the executor
        self.executor = ThreadPoolExecutor(max_workers=size)

    def _handle_request(self, request):
        """
        Handle S3 request and return the result.

        Params:
            - request   An instance of the S3Request object.

        Notes
            - This implementation will execute the request in a different
              thread and return a Future object.
        """
        future = self.executor.submit(request.run)
        return future

    def close(self, wait=True):
        """
        Close the pool.

        Params:
            - Wait      (Optional) Should the close action block until all the
              work is completed? (Defaults to True)
        """
        self.executor.shutdown(wait)

    def as_completed(self, futures, timeout=None):
        """
        Returns an iterator that yields the response for every request when
        it's completed.

        A thin wrapper around concurrent.futures.as_completed.

        Params:
            - futures   A list of Future objects
            - timeout   (Optional) The number of seconds to wait until a
              TimeoutError is raised

        Notes:
            - The order of the results may not be preserved
            - For more information:
                http://docs.python.org/dev/library/
                concurrent.futures.html#concurrent.futures.as_completed
        """
        for r in as_completed(futures, timeout):
            yield r.result()

    def all_completed(self, futures, timeout=None):
        """
        Blocks until all the futures are completed, returns a list of responses

        A thin wrapper around concurrent.futures.wait.

        Params:
            - futures   A list of Future objects
            - timeout   (Optional) The number of seconds to wait until a
              TimeoutError is raised

        Notes:
            - For more information:
                http://docs.python.org/dev/library/
                concurrent.futures.html#concurrent.futures.wait
        """

        results = wait(futures, timeout)[0]  # Return the 'done' set

        return [i.result() for i in results]

    def __enter__(self):
        """
        Context manager implementation
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Closes the pool
        """
        self.close()
