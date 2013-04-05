from multiprocessing import TimeoutError
from multiprocessing.pool import ThreadPool
import threading
import unittest
from flexmock import flexmock
from nose.tools import raises
import time
from tinys3.auth import S3Auth
from tinys3.pool import Pool, AsyncResponse
from .test_conn import TEST_SECRET_KEY, TEST_ACCESS_KEY


class TestPool(unittest.TestCase):
    def test_pool_creation(self):
        """
        Test creating a pool
        """

        # Test new pool with auth
        pool = Pool(TEST_SECRET_KEY, TEST_ACCESS_KEY, default_bucket='bucket', ssl=True)

        self.assertEquals(pool.ssl, True)
        self.assertEquals(pool.default_bucket, 'bucket')
        self.assertTrue(isinstance(pool.auth, S3Auth))
        self.assertTrue(isinstance(pool.pool, ThreadPool))

        # Test new pool with different size
        pool = Pool(TEST_SECRET_KEY, TEST_ACCESS_KEY, size=25)


    def test_async_shortcuts(self):
        """
        Test the 'all_completed'/'as_completed' shortcut methods
        """

        pool = Pool(TEST_SECRET_KEY, TEST_ACCESS_KEY)

        mock = flexmock(AsyncResponse)

        mock.should_receive('as_completed').once()
        pool.as_completed([])

        mock.should_receive('all_completed').once()
        pool.all_completed([])

    def test_pool_as_context_manager(self):
        """
        Test the pool's context_management ability
        """

        pool = Pool(TEST_SECRET_KEY, TEST_ACCESS_KEY)

        flexmock(pool).should_receive('close')

        with pool as p:
            # do nothing
            pass


TEST_RESPONSE = "TEST_RESPONSE"


class TestAsyncResponse(unittest.TestCase):
    def test_create_and_resolve(self):
        """
        The most basic test for getting and setting results
        """
        # Create a new result
        r = AsyncResponse()

        # Should not be ready
        self.assertFalse(r.completed)

        # set the result
        r.resolve(TEST_RESPONSE)

        # Is the result ready
        self.assertTrue(r.completed)

        # test getting the result
        self.assertEqual(r.response(), TEST_RESPONSE)

    @raises(ValueError)
    def test_no_double_set(self):
        """
        Should throw exception if trying to set the result twice
        """

        # Create a new result
        r = AsyncResponse()

        # resolve with the first value
        r.resolve(TEST_RESPONSE)

        # try to resolve again
        r.resolve(TEST_RESPONSE)

        # Should raise an exception

    def test_callback(self):
        """
        Test that a callback is called when setting the result
        """

        cb_result = {}

        # Setup the callback
        def cb(value):
            cb_result['value'] = value
            cb_result['called'] = True

        # Create a result with a callback
        r = AsyncResponse(cb)

        # set the result
        r.resolve(TEST_RESPONSE)

        self.assertTrue(cb_result['called'])
        self.assertEqual(cb_result['value'], TEST_RESPONSE)

    @raises(TimeoutError)
    def test_response_timeout(self):
        """
        Test response with a timeout
        """
        # New result
        r = AsyncResponse()

        # Get the value, with 1 second timeout. this should always fail
        r.response(1)

    def test_add_callback(self):
        """
        Tests adding a callback after the result is created
        """

        r = AsyncResponse()

        cb_result = {}

        # Setup the callback
        def cb(value):
            cb_result['value'] = value
            cb_result['called'] = True

        # Add the callback
        r.add_callback(cb)

        r.resolve(TEST_RESPONSE)

        self.assertTrue(cb_result['called'])
        self.assertEqual(cb_result['value'], TEST_RESPONSE)

    def test_add_callback_after_resolve(self):
        """
        Tests adding a callback after the result is created AND READY
        """

        r = AsyncResponse()

        # Set theh result
        r.resolve(TEST_RESPONSE)

        cb_result = {}

        # Setup the callback
        def cb(value):
            cb_result['value'] = value
            cb_result['called'] = True

        # Add the callback
        r.add_callback(cb)

        self.assertTrue(cb_result['called'])
        self.assertEqual(cb_result['value'], TEST_RESPONSE)

    def test_as_completed_class_method(self):
        """
        Test the 'as_completed' iterator
        """
        responses = []

        for i in range(10):
            responses.append(AsyncResponse())

        # Setup counter
        completed = 0

        # Create a method that will be executed on a different thread
        # And resolve each async response
        def resolver():
            time.sleep(1)
            for i in responses:
                i.resolve(TEST_RESPONSE)

        # Start the resolving thread
        threading.Thread(target=resolver).start()

        for i in AsyncResponse.as_completed(responses):
            self.assertEquals(i, TEST_RESPONSE)
            completed += 1

        # test it was completed
        self.assertEquals(completed, 10)

    def test_all_completed_class_method(self):
        """
        Test the 'all_completed' class method
        """
        responses = []

        for i in range(10):
            responses.append(AsyncResponse())

        # Create a method that will be executed on a different thread
        # And resolve each async response
        def resolver():
            time.sleep(1)
            for i in responses:
                i.resolve(TEST_RESPONSE)

        # Start the resolving thread
        threading.Thread(target=resolver).start()

        results = AsyncResponse.all_completed(responses)

        self.assertEquals(len(results), len(responses))

        for i in results:
            self.assertEquals(i, TEST_RESPONSE)