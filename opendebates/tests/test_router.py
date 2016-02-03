from django.conf import settings
from django.http import HttpRequest
from django.test import TestCase
from django.test.utils import override_settings
from mock import Mock

from opendebates.middleware import DBRoutingMiddleware
from opendebates.routing import DBRouter, is_thread_readwrite, set_thread_readwrite_db, \
    set_thread_readonly_db


class RouterMiddlewareTest(TestCase):
    def test_get_request(self):
        middleware = DBRoutingMiddleware()
        request = Mock(spec=HttpRequest, method='GET')
        output = middleware.process_request(request)
        self.assertIsNone(output)
        self.assertFalse(is_thread_readwrite())

    def test_head_request(self):
        middleware = DBRoutingMiddleware()
        request = Mock(spec=HttpRequest, method='HEAD')
        output = middleware.process_request(request)
        self.assertIsNone(output)
        self.assertFalse(is_thread_readwrite())

    def test_put_request(self):
        middleware = DBRoutingMiddleware()
        request = Mock(spec=HttpRequest, method='PUT')
        output = middleware.process_request(request)
        self.assertIsNone(output)
        self.assertTrue(is_thread_readwrite())

    def test_post_request(self):
        middleware = DBRoutingMiddleware()
        request = Mock(spec=HttpRequest, method='POST')
        output = middleware.process_request(request)
        self.assertIsNone(output)
        self.assertTrue(is_thread_readwrite())


class DBRouterTest(TestCase):
    def setUp(self):
        # In case settings don't have the ones we're going to override
        if not hasattr(settings, 'MASTER_DATABASE'):
            settings.MASTER_DATABASE = ''
        if not hasattr(settings, 'DATABASE_POOL'):
            settings.DATABASE_POOL = {}

    def test_readwrite(self):
        set_thread_readwrite_db()
        master = 'my_master_db'
        with override_settings(MASTER_DATABASE=master):
            router = DBRouter()
            out = router.db_for_read(None)
            self.assertEqual(master, out)
            out = router.db_for_write(None)
            self.assertEqual(master, out)

    def test_readonly_one_slave(self):
        set_thread_readonly_db()
        slave = 'my-only-slave-db'
        pool = {
            slave: 1
        }
        with override_settings(DATABASE_POOL=pool):
            router = DBRouter()
            out = router.db_for_read(None)
            self.assertEqual(slave, out)
            out = router.db_for_write(None)
            self.assertEqual(slave, out)
            out = router.db_for_read(None)
            self.assertEqual(slave, out)
            out = router.db_for_write(None)
            self.assertEqual(slave, out)

    def test_readonly_three_slaves(self):
        set_thread_readonly_db()
        slave0 = 'my-slave-db0'
        slave1 = 'my-slave-db1'
        slave2 = 'my-slave-db2'
        pool = {
            slave0: 1,
            slave1: 1,
            slave2: 1,
        }
        slaves = pool.keys()
        with override_settings(DATABASE_POOL=pool):
            router = DBRouter()
            out0 = router.db_for_read(None)
            self.assertIn(out0, slaves)
            out1 = router.db_for_write(None)
            self.assertIn(out1, slaves)
            self.assertNotEqual(out0, out1)
            out2 = router.db_for_read(None)
            self.assertIn(out2, slaves)
            self.assertNotEqual(out1, out2)
            out3 = router.db_for_write(None)
            # Round-robin should have come around by now
            self.assertEqual(out3, out0)
