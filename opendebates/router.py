import random
import threading
from datetime import datetime, timedelta

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


# The name of the session variable or cookie used by the middleware
PINNING_KEY = getattr(settings, 'MASTER_PINNING_KEY', 'master_db_pinned')

# The number of seconds to direct reads to the master database after a write.
# Under load we can expect the replica(s) to get several seconds or more
# behind, so keep a user who has written to the database on the master
# database for longer than that after their last write.
PINNING_SECONDS = int(getattr(settings, 'MASTER_PINNING_SECONDS', 10))
READONLY_METHODS = ['GET', 'HEAD']

READMOSTLY_MODELS = ['Zipcode', 'Category']


class RoutingState(threading.local):
    """
    Per-thread routing state:
    subclass 'threading.local' so that we can set default values.
    """
    def __init__(self):
        self.read_write = True
        self.written = False

    def is_readwrite(self):
        return self.read_write

    def set_readwrite(self):
        self.read_write = True

    def set_readonly(self):
        self.read_write = False

    def set_written(self):
        self.written = True

    def clear_written(self):
        self.written = False

    def was_written(self):
        return self.written


state = RoutingState()


def is_thread_readwrite():
    return state.is_readwrite()


def set_thread_readonly_db():
    state.set_readonly()


def set_thread_readwrite_db():
    state.set_readwrite()


def set_db_written_flag():
    state.set_written()


def clear_db_written_flag():
    state.clear_written()


def was_db_written():
    return state.was_written()


class DBRoutingMiddleware(object):
    def process_request(self, request):
        clear_db_written_flag()
        pinned_until = request.session.get(PINNING_KEY, False)
        pinned = pinned_until and pinned_until > datetime.now()
        if pinned or request.method not in READONLY_METHODS:
            set_thread_readwrite_db()
        else:
            set_thread_readonly_db()
        return None

    def process_response(self, request, response):
        if was_db_written():
            # Keep the user on the master database for at least PINNING_SECONDS after a write
            request.session[PINNING_KEY] = datetime.now() + timedelta(seconds=PINNING_SECONDS)
            clear_db_written_flag()
        set_thread_readwrite_db()
        return response


class DBRouter(object):
    def __init__(self):
        # Since we default to read-write, if we forget to configure the middleware,
        # things will appear to work, but we won't be routing readonly requests' queries
        # to the replica databases like we want. So catch that case now.
        middleware = 'opendebates.router.DBRoutingMiddleware'
        if middleware not in settings.MIDDLEWARE_CLASSES:
            msg = ("'{}' not in settings MIDDLEWARE_CLASSES. The DBRouter will not work."
                   .format(middleware))
            raise ImproperlyConfigured(msg)

        self.master_db = settings.MASTER_DATABASE
        self.read_dbs = list(settings.DATABASE_POOL.keys())
        random.shuffle(self.read_dbs)
        self.next_db_index = 0
        if not self.read_dbs:
            # No replicas?  Punt.
            self.read_dbs = [self.master_db]

        self.pool = self.read_dbs + [self.master_db]

    def roundrobin_readonly_db(self):
        # Round-robin through the read DBs
        db = self.read_dbs[self.next_db_index]
        self.next_db_index = (self.next_db_index + 1) % len(self.read_dbs)
        return db

    def db_to_use(self, model):
        if is_thread_readwrite():
            return self.master_db
        else:
            return self.roundrobin_readonly_db()

    def db_for_read(self, model, **hints):
        # For a few models that hardly ever ever change, ignore pinning
        # and if we're reading, always go to the replica DB.
        if model._meta.object_name in READMOSTLY_MODELS:
            return self.roundrobin_readonly_db()
        return self.db_to_use(model)

    def db_for_write(self, model, **hints):
        set_db_written_flag()
        return self.db_to_use(model)

    def allow_relation(self, obj1, obj2, **hints):
        """Allow any relation between two objects in the pool"""
        if obj1._state.db in self.pool and obj2._state.db in self.pool:
            return True
        return None

    def allow_syncdb(self, db, model):
        """Explicitly put all models on all databases"""
        return True

    def allow_migrate(self, db, model):
        """Explicitly put all models on all databases"""
        return True
