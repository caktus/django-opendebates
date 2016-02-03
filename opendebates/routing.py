import random
import threading

from django.conf import settings


_locals = threading.local()


def is_thread_readwrite():
    return getattr(_locals, 'is_readwrite', True)


def set_thread_readonly_db():
    _locals.is_readwrite = False


def set_thread_readwrite_db():
    _locals.is_readwrite = True


class DBRouter(object):
    def __init__(self):
        self.master_db = settings.MASTER_DATABASE
        self.read_dbs = list(settings.DATABASE_POOL.keys())
        random.shuffle(self.read_dbs)
        self.next_db_index = 0

    def readwrite_db(self):
        return self.master_db

    def readonly_db(self):
        # Round-robin through the read DBs
        db = self.read_dbs[self.next_db_index]
        self.next_db_index = (self.next_db_index + 1) % len(self.read_dbs)
        return db

    def db_for_read(self, model, **hints):
        if is_thread_readwrite():
            return self.readwrite_db()
        else:
            return self.readonly_db()

    def db_for_write(self, model, **hints):
        if is_thread_readwrite():
            return self.readwrite_db()
        else:
            return self.readonly_db()
