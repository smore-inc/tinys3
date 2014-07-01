# -*- coding: utf-8 -*-

import threading
import unittest
from flexmock import flexmock
from nose.tools import raises
import time
from tinys3.auth import S3Auth
from tinys3.pool import Pool
from .test_conn import TEST_SECRET_KEY, TEST_ACCESS_KEY
from concurrent.futures import ThreadPoolExecutor, Future
import concurrent.futures

DUMMY_OBJECT = 'DUMMY'


class TestPool(unittest.TestCase):
    def test_pool_creation(self):
        """
        Test creating a pool
        """

        # Test new pool with auth
        pool = Pool(TEST_ACCESS_KEY, TEST_SECRET_KEY, default_bucket='bucket', tls=True)

        self.assertEquals(pool.tls, True)
        self.assertEquals(pool.default_bucket, 'bucket')
        self.assertTrue(isinstance(pool.auth, S3Auth))
        self.assertTrue(isinstance(pool.executor, ThreadPoolExecutor))

        # Test new pool with different size
        pool = Pool(TEST_ACCESS_KEY, TEST_SECRET_KEY, size=25)
        self.assertEquals(pool.executor._max_workers, 25)


    def test_as_completed(self):
        """
        Test the as_completed method
        """

        # Create mock futures
        futures = [Future(), Future(), Future()]

        # Create a default pool
        pool = Pool(TEST_ACCESS_KEY, TEST_SECRET_KEY)

        # Resolve futures with a simple object
        for i in futures:
            i.set_result(DUMMY_OBJECT)

        # Make sure all the results are dummy objects
        for i in pool.as_completed(futures):
            self.assertEquals(i, DUMMY_OBJECT)

    def test_all_completed(self):
        """
        Test the all completed
        """
        # Create mock futures
        futures = [Future(), Future(), Future()]

        # Create a default pool
        pool = Pool(TEST_ACCESS_KEY, TEST_SECRET_KEY)

        # Resolve futures with a simple object
        for i in futures:
            i.set_result(DUMMY_OBJECT)

        # Make sure all the results are dummy objects
        for i in pool.all_completed(futures):
            self.assertEquals(i, DUMMY_OBJECT)

    def test_pool_as_context_manager(self):
        """
        Test the pool's context_management ability
        """

        pool = Pool(TEST_ACCESS_KEY, TEST_SECRET_KEY)

        flexmock(pool).should_receive('close').once()

        with pool as p:
            # do nothing
            pass