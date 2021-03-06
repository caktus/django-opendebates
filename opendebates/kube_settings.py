"""
Should set in env:

SECRET_KEY
EMAIL_HOST
EMAIL_HOST_USER
EMAIL_HOST_PASSWORD
DEPLOYMENT_TAG
ENVIRONMENT
DEFAULT_FROM_EMAIL
MEMCACHED_HOST
REDIS_HOST
NORECAPTCHA_SITE_KEY
NORECAPTCHA_SECRET_KEY
USE_CAPTCHA ("0" or "1")
MIXPANEL_KEY
OPTIMIZELY_KEY
"""

from __future__ import absolute_import
from .settings import *  # noqa: F403
from .settings import ALLOWED_HOSTS, CELERYBEAT_SCHEDULE

from celery.schedules import crontab
import os
import dj_database_url


DATABASES = {
    'default': dj_database_url.config(env="DATABASE_URL", conn_max_age=600),
}

# media roots
# MEDIA_ROOT = "{{ media_root }}"
# STATIC_ROOT = "{{ static_root }}"
# email settings
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.postmarkapp.com")
EMAIL_PORT = 587
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")
EMAIL_USE_TLS = True

ENVIRONMENT = os.getenv("ENVIRONMENT")

EMAIL_SUBJECT_PREFIX = "[%s %s] " % (
    os.getenv("DEPLOYMENT_TAG"),
    ENVIRONMENT,
)
ADMINS = [("Caktus Opendebates team", "opendebates-team@caktusgroup.com")]
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL")
SERVER_EMAIL = DEFAULT_FROM_EMAIL

# Redis DB map:
# 0 = cache
# 1 = unused (formerly celery task queue)
# 2 = celery results
# 3 = session store
# 4-16 = (free)

# Cache settings
CACHES = {}
CACHES["default"] = {
    "BACKEND": "django.core.cache.backends.memcached.MemcachedCache",
    "LOCATION": "%s:11211" % os.getenv("MEMCACHED_HOST", "memcached"),
    # 'VERSION': '{{ current_changeset }}',
}
CACHES["session"] = {
    "BACKEND": "redis_cache.RedisCache",
    "LOCATION": "%s:6379" % os.getenv("REDIS_HOST", "redis"),
    "OPTIONS": {"DB": 3},
}

# https://cache-machine.readthedocs.org/en/latest/index.html#object-creation:
CACHE_INVALIDATE_ON_CREATE = "whole-model"

# Task queue settings

# see https://github.com/ask/celery/issues/436 (sorry, that's now a 404)
BROKER_URL = "redis://%s:6379/0" % os.getenv("REDIS_HOST")
CELERY_RESULT_BACKEND = "redis://%s:6379/2" % os.getenv("REDIS_HOST")
BROKER_CONNECTION_TIMEOUT = 4
BROKER_POOL_LIMIT = 10

# Session settings
SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "session"

if "DBBACKUP_STORAGE" in os.environ:
    DBBACKUP_FILENAME_TEMPLATE = os.getenv("DBBACKUP_FILENAME_TEMPLATE")
    DBBACKUP_STORAGE = os.getenv("DBBACKUP_STORAGE")
    # Note: to write to this Google Storage bucket, GOOGLE_APPLICATION_CREDENTIALS should
    # be set in the environment; see the README.
    DBBACKUP_STORAGE_OPTIONS = {
        "bucket_name": os.getenv("DBBACKUP_STORAGE_OPTIONS_GS_BUCKET_NAME"),
    }
    CELERYBEAT_SCHEDULE["backup-database"] = {
        "task": "opendebates.tasks.backup_database",
        "schedule": crontab(minute=0, hour="*/4"),  # backup database every 4 hours
        'options': {
            # If no worker runs it before the next scheduled run, throw it away; more
            # tasks will already have been scheduled.
            'expires': 3600 * 3,  # 3 hours, in seconds
        }
    }
    # dbbackup needs this to send email
    DBBACKUP_HOSTNAME = ALLOWED_HOSTS[0]

NORECAPTCHA_SITE_KEY = os.getenv("NORECAPTCHA_SITE_KEY")
NORECAPTCHA_SECRET_KEY = os.getenv("NORECAPTCHA_SECRET_KEY")
USE_CAPTCHA = bool(int(os.getenv("USE_CAPTCHA", "0")))
MIXPANEL_KEY = os.getenv("MIXPANEL_KEY")
OPTIMIZELY_KEY = os.getenv("OPTIMIZELY_KEY")

if ENVIRONMENT in SITE_THEMES:  # noqa: F405
    SITE_THEME_NAME = ENVIRONMENT
else:
    SITE_THEME_NAME = "testing"
