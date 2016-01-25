# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
import sys
from django.utils.translation import ugettext_lazy as _
import dj_database_url
import djcelery

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIXTURE_DIRS = [os.path.join(BASE_DIR, 'fixtures')]

SECRET_KEY = 'dg0pdghh4andk^v=rw^l-i81yz-h2co%mlj4)+p(cqz@d&0i$2'  # @@TODO

DEBUG = TEMPLATE_DEBUG = 'DJANGO_DEBUG' in os.environ

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
    'opendebates',
    'opendebates_comments',
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
        'DIRS': [],
        'APP_DIRS': True,
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
djcelery.setup_loader()

CELERY_SEND_TASK_ERROR_EMAILS = True

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

if 'test' in sys.argv:
    PIPELINE_COMPILERS = ()

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
