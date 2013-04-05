from datetime import time
from multiprocessing import TimeoutError
import threading
from .conn import Base
from multiprocessing.pool import ThreadPool
from requests import Session

# Support for python 2/3
try:
    from Queue import Queue
except ImportError:
    from queue import Queue


def async_handle_request(request):
    with Session() as s:
        return s.send(request)


class Pool(Base):
    def __init__(self, secret_key, access_key, default_bucket=None, ssl=False, size=5):
        super(Pool, self).__init__(secret_key, access_key, ssl=ssl, default_bucket=default_bucket)

        self.pool = ThreadPool(processes=size)

    def _handle_request(self, request):
        async_response = AsyncResponse()

        self.pool.apply_async(async_handle_request, [request],
                              callback=lambda response: async_response.resolve(response))

        return async_response

    def close(self, wait=True):
        self.pool.close()
        if wait:
            self.pool.join()

    def as_completed(self, async_responses, timeout=None):
        return AsyncResponse.as_completed(async_responses, timeout)

    def all_completed(self, async_responses, timeout=None):
        return AsyncResponse.all_completed(async_responses, timeout)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class AsyncResponse(object):
    """
    A result for an S3 job with support for async handling

    Notes:
     - The locking/timeout mechanism code was copied from Python's multiprocessing ApplyAsync code
    """

    def __init__(self, callback=None):
        self._response = None
        self._completed = False

        # Our lock condition
        self._cond = threading.Condition(threading.Lock())

        self._callbacks = []

        if callable(callback):
            self._callbacks.append(callback)

    def resolve(self, value):
        """
        Set the value of the AsyncResponse object

        Params:
            - value     The desired value
            - success   is this a successful result?
        """

        # Sanity, check that we're not setting an already set value
        if self._completed:
            raise ValueError("Can't set an already set value!")

        # Store the value
        self._response = value

        self._cond.acquire()
        try:
            self._completed = True
            self._cond.notify()
        finally:
            self._cond.release()

        # Invoke callback
        for c in self._callbacks:
            c(self._response)

    @property
    def completed(self):
        """
        Is the result ready?
        """
        return self._completed


    def wait(self, timeout=None):
        """
        Wait to the result to be completed.

        Params:
            - timeout   The number of seconds to wait for the result to complete

        Notes:
            - This is a low level method for waiting to the result, if you just want
              the result, use response()

            - As this method will always catch the timeout exception, you should ALWAYS check
              that the result is ready after this method returns!
        """
        self._cond.acquire()
        try:
            if not self._completed:
                self._cond.wait(timeout)
        finally:
            self._cond.release()

    def response(self, timeout=None):
        """
         Get the result, if it's set
        """
        self.wait(timeout)
        if not self._completed:
            raise TimeoutError

        return self._response

    def add_callback(self, callback):
        """
        Add another callback to the result

        Params:
            - callback  a callable object that will function as the callback

        Notes:
            - If the result is already completed, the callback will be invoked immediately
        """
        # Make sure the callback is callable
        assert callable(callback)

        # if not ready yet, append to callbacks
        if not self.completed:
            self._callbacks.append(callback)
        else:
            # Call it immediately
            callback(self._response)


    @classmethod
    def all_completed(cls, async_responses, timeout=None):
        """
        Wait for all the async responses to complete, return a list with the responses
        """

        queue = TimeoutQueue()

        for r in async_responses:
            queue.put('DUMMY_VALUE')
            r.add_callback(lambda response: queue.task_done())

        # Wait until everything is completed
        queue.join_queue(timeout=timeout)

        return list(r.response() for r in async_responses)

    @classmethod
    def as_completed(cls, async_responses, timeout=None):
        """
        A generator that return responses as they are completed
        """

        queue = Queue()

        pending = len(async_responses)

        for r in async_responses:
            r.add_callback(lambda response: queue.put(response))

        while pending > 0:
            yield queue.get(timeout=timeout)
            pending -= 1


class TimeoutQueue(Queue):
    """
    A simple class to implement Timeout queue
    """

    def join_queue(self, timeout=None):
        self.all_tasks_done.acquire()
        try:
            if timeout is None:
                while self.unfinished_tasks:
                    self.all_tasks_done.wait()
            elif timeout < 0:
                raise ValueError("'timeout' must be a positive number")
            else:
                endtime = time() + timeout
                while self.unfinished_tasks:
                    remaining = endtime - time()
                    if remaining <= 0.0:
                        raise TimeoutError
                    self.all_tasks_done.wait(remaining)
        finally:
            self.all_tasks_done.release()