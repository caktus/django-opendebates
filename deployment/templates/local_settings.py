from __future__ import absolute_import

from celery.schedules import crontab

from opendebates.settings import *

DEBUG = False

# logging settings
#LOGGING['filters']['static_fields']['fields']['deployment'] = '{{ deployment_tag }}'
#LOGGING['filters']['static_fields']['fields'][''] = '{{ environment }}'
#LOGGING['filters']['static_fields']['fields']['role'] = '{{ current_role }}'
# AWS_STORAGE_BUCKET_NAME = '{{ staticfiles_s3_bucket }}'
# AWS_ACCESS_KEY_ID = 'AKIAI3XJKABCOBWLX33A'
# AWS_SECRET_ACCESS_KEY = "{{ s3_secret }}"

SECRET_KEY = "{{ secret_key }}"

# Tell django-storages that when coming up with the URL for an item in S3 storage, keep
# it simple - just use this domain plus the path. (If this isn't set, things get complicated).
# This controls how the `static` template tag from `staticfiles` gets expanded, if you're using it.
# We also use it in the next setting.
# AWS_S3_CUSTOM_DOMAIN = '%s.s3.amazonaws.com' % AWS_STORAGE_BUCKET_NAME

# This is used by the `static` template tag from `static`, if you're using that. Or if anything else
# refers directly to STATIC_URL. So it's safest to always set it.
#STATIC_URL = "https://%s/" % AWS_S3_CUSTOM_DOMAIN
# (STATIC_URL is set in settings.py to /static/ which is fine without S3)

# Tell the staticfiles app to use S3Boto storage when writing the collected static files (when
# you run `collectstatic`).
#STATICFILES_STORAGE = 'opendebates.storage.S3PipelineCachedStorage'

# Auto-create the bucket if it doesn't exist
# AWS_AUTO_CREATE_BUCKET = True

# AWS_HEADERS = {  # see http://developer.yahoo.com/performance/rules.html#expires
#     'Expires': 'Thu, 31 Dec 2099 20:00:00 GMT',
#     'Cache-Control': 'max-age=94608000',
# }

# Having AWS_PRELOAD_META turned on breaks django-storages/s3 -
# saving a new file doesn't update the metadata and exists() returns False
#AWS_PRELOAD_METADATA = True

# database settings
DATABASES = {
{% for server in all_databases %}
    '{{ server.database_key }}': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': '{{ server.database_local_name }}',
        'USER': '{{ database_user }}',
        'PASSWORD': '{{ database_password }}',
        'HOST': 'localhost',
        'PORT': '{{ pgbouncer_port }}',
    },{% endfor %}
}

# django-balancer settings
DATABASE_POOL = {
{% for server in slave_databases %}
    '{{ server.database_key }}': 1,{% endfor %}
}
MASTER_DATABASE = '{{ master_database.database_key }}'
DATABASE_ROUTERS = [
    'opendebates.router.DBRouter',
]

# media roots
MEDIA_ROOT = "{{ media_root }}"
STATIC_ROOT = "{{ static_root }}"


# email settings
EMAIL_HOST = 'smtp.postmarkapp.com'
EMAIL_PORT = 587
EMAIL_HOST_USER = '{{ smtp_password }}'
EMAIL_HOST_PASSWORD = '{{ smtp_password }}'
EMAIL_USE_TLS = True

EMAIL_SUBJECT_PREFIX = '[{{ deployment_tag }} {{ environment }}] '
ADMINS = [
    ('Caktus Opendebates team', 'opendebates-team@caktusgroup.com'),
]
DEFAULT_FROM_EMAIL = '{{ email_from }}'
SERVER_EMAIL = DEFAULT_FROM_EMAIL

# Redis DB map:
# 0 = cache
# 1 = unused (formerly celery task queue)
# 2 = celery results
# 3 = session store
# 4-16 = (free)

# Cache settings
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': '{{ cache_server.internal_ip }}:11211',
        'VERSION': '{{ current_changeset }}',
    },
    'session': {
        'BACKEND': 'redis_cache.RedisCache',
        'LOCATION': '{{ cache_server.internal_ip }}:6379',
        'OPTIONS': {
            'DB': 3,
        },
    },
}

# https://cache-machine.readthedocs.org/en/latest/index.html#object-creation:
CACHE_INVALIDATE_ON_CREATE = 'whole-model'

# Task queue settings

# see https://github.com/ask/celery/issues/436
BROKER_URL = "amqp://{{ deploy_user }}:{{ broker_password }}@{{ cache_server.internal_ip }}:5672/{{ vhost }}"
BROKER_CONNECTION_TIMEOUT = 4
BROKER_POOL_LIMIT = 10
CELERY_RESULT_BACKEND = "redis://{{ cache_server.internal_ip }}:6379/2"

# Session settings
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'session'

ALLOWED_HOSTS = [{% for host in allowed_hosts %}'{{ host }}', {% endfor %}]



LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'formatters': {
        'basic': {
            'format': '%(asctime)s %(name)-20s %(levelname)-8s %(message)s',
        },
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'basic',
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
        'django.security': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    },
    'root': {
        'handlers': ['console', ],
        'level': 'INFO',
    },
}


CELERYBEAT_SCHEDULE["backup-database"] = {
    "task": "opendebates.tasks.backup_database",
    "schedule": crontab(minute=0, hour="*/4"), # backup database every 4 hours
}

DBBACKUP_DATABASES = [MASTER_DATABASE]

DBBACKUP_STORAGE = 'dbbackup.storage.s3_storage'
DBBACKUP_STORAGE_OPTIONS = {
    'access_key': '{{ dbbackup_access_key }}',
    'secret_key': '{{ dbbackup_access_secret }}',
    'bucket_name': 'opendebates-backups'
}

DBBACKUP_FILENAME_TEMPLATE = '{{ environment }}/{datetime}.{extension}'
DBBACKUP_SEND_EMAIL = True
# dbbackup needs this to send email
DBBACKUP_HOSTNAME = ALLOWED_HOSTS[0]

NORECAPTCHA_SITE_KEY = '{{ recaptcha_site_key }}'
NORECAPTCHA_SECRET_KEY = '{{ recaptcha_secret }}'
USE_CAPTCHA = {{ use_captcha|default(true) }}
MIXPANEL_KEY = '{{ mixpanel_key }}'
OPTIMIZELY_KEY = '{{ optimizely_key }}'

# don't customize SITE_THEME, which will make testing use 'florida' theme hardcoded in main settings file
# SITE_THEME_NAME = '{{ environment }}'
# SITE_THEME = SITE_THEMES[SITE_THEME_NAME]
SITE_DOMAIN = '{{ site_domains[0] }}'
SITE_DOMAIN_WITH_PROTOCOL = "https://" + SITE_DOMAIN
