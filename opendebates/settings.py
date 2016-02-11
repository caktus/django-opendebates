# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
from datetime import timedelta
import os
import sys
from django.utils.translation import ugettext_lazy as _
import dj_database_url

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIXTURE_DIRS = [os.path.join(BASE_DIR, 'fixtures')]

# SECRET_KEY is overriden in deploy settings
SECRET_KEY = 'secret-key-for-local-use-only'

DEBUG = 'DJANGO_DEBUG' in os.environ
TRAVIS = 'TRAVIS' in os.environ

ALLOWED_HOSTS = []

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'django.contrib.flatpages',
    'pipeline',
    'djangobower',
    'dbbackup',
    'nocaptcha_recaptcha',
    # Still using django-celery because that's how Fabulaws starts workers
    'djcelery',
    'opendebates',
    'opendebates_emails',
    'djorm_pgfulltext',
    'endless_pagination',
    'bootstrapform',
    'registration',
]

if DEBUG:
    INSTALLED_APPS.append('debug_toolbar')

if DEBUG:
    MIDDLEWARE_CLASSES = []
else:
    MIDDLEWARE_CLASSES = [
        'django.middleware.gzip.GZipMiddleware',
    ]
MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.flatpages.middleware.FlatpageFallbackMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'opendebates.router.DBRoutingMiddleware',
)

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'opendebates.authentication_backend.EmailAuthBackend',
    ]


ROOT_URLCONF = 'opendebates.urls'

LOGIN_URL = LOGIN_ERROR_URL = "/registration/login/"


TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'opendebates.context_processors.global_vars',
                'opendebates.context_processors.voter',
            ],
        },
    },
]

if DEBUG:
    # APP_DIRS must be set when not using the cached Loader
    TEMPLATES[0]['APP_DIRS'] = True
else:
    # Use the cached Loader for deployment
    TEMPLATES[0]['OPTIONS']['loaders'] = [
        ('django.template.loaders.cached.Loader', [
            'django.template.loaders.app_directories.Loader',
        ]),
    ]

WSGI_APPLICATION = 'opendebates.wsgi.application'

DATABASES = {
    'default': dj_database_url.config(default="postgres://@/opendebates"),
}

if DEBUG is True:
    DEBUG_TOOLBAR_CONFIG = {
        'SHOW_TOOLBAR_CALLBACK': "%s.true" % __name__,
    }

    def true(request):
        return True

    class AllIPS(list):
        def __contains__(self, item):
            return True

    INTERNAL_IPS = AllIPS()

# Internationalization
LANGUAGES = (
    ('en', _('English')),
)
LANGUAGE_CODE = 'en-us'
LOCALE_PATHS = (os.path.join(BASE_DIR, 'locale'),)
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# celery settings
CELERY_SEND_TASK_ERROR_EMAILS = True
CELERY_ALWAYS_EAGER = DEBUG or TRAVIS
CELERY_EAGER_PROPAGATES_EXCEPTIONS = True
CELERY_IGNORE_RESULT = True
CELERYD_HIJACK_ROOT_LOGGER = False
CELERYBEAT_SCHEDULE = {
    'update_recent_events': {
        'task': 'opendebates.tasks.update_recent_events',
        'schedule': timedelta(seconds=10),
        'options': {
            # If no worker runs it within 60 seconds, throw it away; more
            # tasks will already have been scheduled.
            'expires': 60,  # seconds
        }
    },
    'update_trending_scores': {
        'task': 'opendebates.tasks.update_trending_scores',
        'schedule': timedelta(minutes=10),
        'options': {
            # If no worker runs it within 10 minutes, throw it away; more
            # tasks will already have been scheduled.
            'expires': 60 * 10,  # seconds
        }
    },
}

STATICFILES_STORAGE = 'pipeline.storage.PipelineCachedStorage'

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'pipeline.finders.PipelineFinder',
    'djangobower.finders.BowerFinder',
)

PIPELINE_COMPILERS = (
    'pipeline.compilers.less.LessCompiler',
)

if DEBUG:
    PIPELINE_CSS_COMPRESSOR = None
    PIPELINE_JS_COMPRESSOR = None

PIPELINE_CSS = {
    'base': {
        'source_filenames': (
            'less/base.less',
        ),
        'output_filename': 'css/base.css',
        'extra_context': {
            'media': 'screen,projection',
        },
    },
    'login': {
        'source_filenames': (
            'less/login.less',
        ),
        'output_filename': 'css/login.css',
        'extra_context': {
            'media': 'screen,projection',
        },
    },
}

PIPELINE_JS = {
    'base': {
        'source_filenames': (
            'js/base/*.js',
            'templates/base/*.handlebars',
        ),
        'output_filename': 'js/base.js',
    },
    'home': {
        'source_filenames': (
            'js/home.js',
        ),
        'output_filename': 'js/home.js',
    },
    'login': {
        'source_filenames': (
            'js/login.js',
        ),
        'output_filename': 'js/login.js',
    }

}

PIPELINE_TEMPLATE_EXT = '.handlebars'
PIPELINE_TEMPLATE_FUNC = 'Handlebars.compile'
PIPELINE_TEMPLATE_NAMESPACE = 'Handlebars.templates'

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

BOWER_COMPONENTS_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "static"),
)

BOWER_INSTALLED_APPS = (
    'jquery',
    'lodash',
    'bootstrap',
    'moment',
    'handlebars',
)

SITE_ID = 1
SITE_DOMAIN = os.environ.get("SITE_DOMAIN", "127.0.0.1:8000")
SITE_DOMAIN_WITH_PROTOCOL = os.environ.get("SITE_PROTOCOL", "http://") + SITE_DOMAIN

if 'test' in sys.argv:
    PIPELINE_COMPILERS = ()
    PIPELINE_ENABLED = False

# Cache settings for when we're not deployed. Otherwise, local_settings will override this.
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': '127.0.0.1:11211',
        'VERSION': '0',
    },

}

# For running 'dbbackup' locally
DBBACKUP_STORAGE = 'dbbackup.storage.filesystem_storage'
DBBACKUP_STORAGE_OPTIONS = {'location': '.'}
DBBACKUP_FILENAME_TEMPLATE = 'local/{datetime}.{extension}'
DBBACKUP_SEND_EMAIL = False
