from datetime import datetime, timedelta

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpRequest
from django.test import TestCase
from django.test.utils import override_settings
from mock import Mock

from opendebates.models import Submission
from opendebates.router import DBRouter, is_thread_readwrite, set_thread_readwrite_db, \
    set_thread_readonly_db, set_db_written_flag, was_db_written, clear_db_written_flag, \
    DBRoutingMiddleware, PINNING_KEY, readwrite_db, readonly_db


class RouterMiddlewareTest(TestCase):
    def test_get_request(self):
        # Get request uses replica DB if not pinned
        middleware = DBRoutingMiddleware()
        request = Mock(spec=HttpRequest, method='GET')
        request.session = {}
        output = middleware.process_request(request)
        self.assertIsNone(output)
        self.assertFalse(is_thread_readwrite())

    def test_get_request_pinned(self):
        # If session is pinned, use master DB
        middleware = DBRoutingMiddleware()
        request = Mock(spec=HttpRequest, method='GET')
        request.session = {
            PINNING_KEY: datetime.now() + timedelta(seconds=30)
        }
        output = middleware.process_request(request)
        self.assertIsNone(output)
        self.assertTrue(is_thread_readwrite())

    def test_head_request(self):
        middleware = DBRoutingMiddleware()
        request = Mock(spec=HttpRequest, method='HEAD')
        request.session = {}
        output = middleware.process_request(request)
        self.assertIsNone(output)
        self.assertFalse(is_thread_readwrite())

    def test_put_request(self):
        middleware = DBRoutingMiddleware()
        request = Mock(spec=HttpRequest, method='PUT')
        request.session = {}
        output = middleware.process_request(request)
        self.assertIsNone(output)
        self.assertTrue(is_thread_readwrite())

    def test_post_request_without_write(self):
        middleware = DBRoutingMiddleware()
        request = Mock(spec=HttpRequest, method='POST')
        request.session = {}
        output = middleware.process_request(request)
        self.assertIsNone(output)
        self.assertTrue(is_thread_readwrite())
        response = Mock()
        output = middleware.process_response(request, response)
        self.assertEqual(output, response)
        # No write - did not pin
        self.assertNotIn(PINNING_KEY, request.session)

    def test_post_request_with_write(self):
        middleware = DBRoutingMiddleware()
        request = Mock(spec=HttpRequest, method='POST')
        request.session = {}
        output = middleware.process_request(request)
        self.assertIsNone(output)
        self.assertTrue(is_thread_readwrite())
        set_db_written_flag()
        response = Mock()
        output = middleware.process_response(request, response)
        self.assertEqual(output, response)
        # Db was written, so pin
        self.assertTrue(request.session[PINNING_KEY] > datetime.now())


class DBRouterTest(TestCase):
    def setUp(self):
        # In case settings don't have the ones we're going to override
        if not hasattr(settings, 'MASTER_DATABASE'):
            settings.MASTER_DATABASE = ''
        if not hasattr(settings, 'DATABASE_POOL'):
            settings.DATABASE_POOL = {}
        clear_db_written_flag()

    def test_middleware_validation(self):
        # The router raises an error if the necessary middleware is not configured.
        with override_settings(MIDDLEWARE_CLASSES=[]):
            with self.assertRaises(ImproperlyConfigured):
                DBRouter()

    def test_writing_sets_db_written_flag(self):
        router = DBRouter()
        router.db_for_read(Submission)
        self.assertFalse(was_db_written())
        router.db_for_write(Submission)
        self.assertTrue(was_db_written())
        # A read won't reset the flag
        router.db_for_read(Submission)
        self.assertTrue(was_db_written())

    def test_readwrite(self):
        self.assertFalse(was_db_written())
        set_thread_readwrite_db()
        master = 'my_master_db'
        with override_settings(MASTER_DATABASE=master):
            router = DBRouter()
            out = router.db_for_read(Submission)
            self.assertEqual(master, out)
            out = router.db_for_write(Submission)
            self.assertEqual(master, out)
        self.assertTrue(was_db_written())

    def test_readonly_one_replica(self):
        set_thread_readonly_db()
        replica = 'my-only-replica-db'
        pool = {
            replica: 1
        }
        with override_settings(DATABASE_POOL=pool):
            router = DBRouter()
            out = router.db_for_read(Submission)
            self.assertEqual(replica, out)
            out = router.db_for_read(Submission)
            self.assertEqual(replica, out)
        self.assertFalse(was_db_written())

    def test_readonly_three_replicas(self):
        set_thread_readonly_db()
        replica0 = 'my-replica-db0'
        replica1 = 'my-replica-db1'
        replica2 = 'my-replica-db2'
        pool = {
            replica0: 1,
            replica1: 1,
            replica2: 1,
        }
        replicas = pool.keys()
        with override_settings(DATABASE_POOL=pool):
            router = DBRouter()
            out0 = router.db_for_read(Submission)
            self.assertIn(out0, replicas)
            out1 = router.db_for_read(Submission)
            self.assertIn(out1, replicas)
            self.assertNotEqual(out0, out1)
            out2 = router.db_for_read(Submission)
            self.assertIn(out2, replicas)
            self.assertNotEqual(out1, out2)
            out3 = router.db_for_read(Submission)
            # Round-robin should have come around by now
            self.assertEqual(out3, out0)
        self.assertFalse(was_db_written())


class ContextManagerTest(TestCase):
    def test_with_readwrite_db_when_readonly(self):
        set_thread_readonly_db()
        assert not is_thread_readwrite()
        with readwrite_db():
            assert is_thread_readwrite()
        assert not is_thread_readwrite()

    def test_with_readwrite_db_when_readwrite(self):
        set_thread_readwrite_db()
        assert is_thread_readwrite()
        with readwrite_db():
            assert is_thread_readwrite()
        assert is_thread_readwrite()

    def test_with_readonly_db_when_readonly(self):
        set_thread_readonly_db()
        assert not is_thread_readwrite()
        with readonly_db():
            assert not is_thread_readwrite()
        assert not is_thread_readwrite()

    def test_with_readonly_db_when_readwrite(self):
        set_thread_readwrite_db()
        assert is_thread_readwrite()
        with readonly_db():
            assert not is_thread_readwrite()
        assert is_thread_readwrite()

    def test_nesting(self):
        set_thread_readwrite_db()
        assert is_thread_readwrite()
        with readonly_db():
            assert not is_thread_readwrite()
            with readwrite_db():
                assert is_thread_readwrite()
            assert not is_thread_readwrite()
        assert is_thread_readwrite()
