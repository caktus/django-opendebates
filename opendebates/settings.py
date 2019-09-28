# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
from datetime import timedelta
import os
import sys
from django.utils.translation import ugettext_lazy as _
import dj_database_url

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIXTURE_DIRS = [os.path.join(BASE_DIR, 'fixtures')]

# Both DOMAIN variables are overwritten in local_settings.py

SUBMISSIONS_PER_PAGE = 25

SITE_THEMES = ['testing', 'florida']
SITE_THEME_NAME = 'florida'
# SITE_THEME_NAME gets overriden in local_settings

ENABLE_USER_DISPLAY_NAME = False
ENABLE_USER_PHONE_NUMBER = True

# SECRET_KEY is overriden in deploy settings
SECRET_KEY = os.getenv('SECRET_KEY', 'secret-key-for-local-use-only')

TEST = 'test' in sys.argv
if TEST:
    # https://docs.djangoproject.com/en/1.8/topics/testing/overview/#other-test-conditions
    # DEBUG is False for tests no matter what we set, so set it up properly for
    # use later in this file
    DEBUG = False
else:
    DEBUG = 'DJANGO_DEBUG' in os.environ

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost:8000').split(',')

INSTALLED_APPS = [
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
    'el_pagination',
    'bootstrapform',
    'registration',
    # more django apps, that we want to override template of
    'django.contrib.admin',
]

if DEBUG:
    INSTALLED_APPS.append('debug_toolbar')

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
    'opendebates.middleware.DebateMiddleware',
)

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'opendebates.authentication_backend.EmailAuthBackend',
    ]


ROOT_URLCONF = 'opendebates.urls'

LOGIN_URL = LOGIN_ERROR_URL = 'auth_login'

LOGIN_REDIRECT_URL = 'list_ideas'


TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.request',  # For EL-pagination
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

if DEBUG:
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
TIME_ZONE = 'America/New_York'
USE_I18N = True
USE_L10N = False
USE_TZ = True
USE_THOUSAND_SEPARATOR = True

# celery settings
CELERY_SEND_TASK_ERROR_EMAILS = True
CELERY_ALWAYS_EAGER = DEBUG or TEST
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

if TEST:
    STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
    STATICFILES_FINDERS = (
        'django.contrib.staticfiles.finders.FileSystemFinder',
        'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    )

# Settings for Django-pipeline
PIPELINE = {
    'JAVASCRIPT': {
        'base': {
            'source_filenames': (
                'js/base/*.js',
                'templates/base/*.handlebars',
            ),
            'output_filename': 'js/base.js',
        },
        'registration': {
            'source_filenames': (
                'js/registration.js',
            ),
            'output_filename': 'js/registration.js',
        }
    },
    'STYLESHEETS': {
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
    },
    'CSS': {
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
    },
    'TEMPLATE_EXT': '.handlebars',
    'TEMPLATE_FUNC': 'Handlebars.compile',
    'TEMPLATE_NAMESPACE': 'Handlebars.templates',
    'COMPILERS': (
        'pipeline.compilers.less.LessCompiler',
    ),
}

if DEBUG:
    PIPELINE['CSS_COMPRESSOR'] = None
    PIPELINE['PIPELINE_JS_COMPRESSOR'] = None

if TEST:
    PIPELINE['COMPILERS'] = ()
    PIPELINE['ENABLED'] = False

for theme in SITE_THEMES:
    PIPELINE['STYLESHEETS']['theme-%s' % (theme,)] = {
        'source_filenames': (
            'less/theme-%s.less' % (theme,),
        ),
        'output_filename': 'css/theme-%s.css' % (theme,),
        'extra_context': {
            'media': 'screen,projection',
        },
    }

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

BOWER_COMPONENTS_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "static"),
)

BOWER_INSTALLED_APPS = (
    'jquery',
    'lodash',
    'bootstrap',
    'bootstrap-select',
    'moment',
    'handlebars',
)

# Cache settings for when we're not deployed. Otherwise, local_settings will override this.
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    },

}

# For running 'dbbackup' locally
DBBACKUP_STORAGE = 'dbbackup.storage.filesystem_storage'
DBBACKUP_STORAGE_OPTIONS = {'location': '.'}
DBBACKUP_FILENAME_TEMPLATE = 'local/{datetime}.{extension}'
DBBACKUP_SEND_EMAIL = False

# With the following test keys, you will always get No CAPTCHA and all verification requests
# will pass.
# https://developers.google.com/recaptcha/docs/faq#id-like-to-run-automated-test-with-recaptcha-v2-how-should-i-do
NORECAPTCHA_SITE_KEY = '6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI'
NORECAPTCHA_SECRET_KEY = '6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe'

MIXPANEL_KEY = None
OPTIMIZELY_KEY = None

# Turn this off to never use CAPTCHA
USE_CAPTCHA = True

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

SECURE_SSL_REDIRECT = not TEST and not DEBUG
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
