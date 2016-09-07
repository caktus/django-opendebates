# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
from datetime import timedelta
import os
import sys
from textwrap import dedent
from django.utils.translation import ugettext_lazy as _
import dj_database_url

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIXTURE_DIRS = [os.path.join(BASE_DIR, 'fixtures')]

SITE_ID = 1
SITE_DOMAIN = os.environ.get("DOMAIN", os.environ.get("SITE_DOMAIN", "127.0.0.1:8000"))
SITE_DOMAIN_WITH_PROTOCOL = "https://" + SITE_DOMAIN
# Both DOMAIN variables are overwritten in local_settings.py

SUBMISSIONS_PER_PAGE = 25

SITE_THEMES = {
    'florida': {
        "HASHTAG": u"FLOpenDebate",
        "HEADER_TITLE": _(u"WELCOME TO THE\nFLORIDA OPEN DEBATE"),
        "HEADER_COPY": _(
            u"Ask Congressman David Jolly (R-FL) and Congressman Alan Grayson (D-FL) about "
            u"the issues that are most important "
            "to you -- then vote and tell others! Watch the Florida Open Debate for U.S. "
            "Senate right here on Monday, April 25, at 7:00 pm EDT. All questions "
            "will be chosen from among those that receive the most votes online."),

        "AFTER_QUESTION_SUBMITTED_TEXT": _(
            u"Next, help your question collect votes. Share it on social media "
            u"and email it to friends. For the live event, all questions will be "
            u"chosen from among the Top 30 that received the most votes (and no "
            u"more than the Top 5 in each category)."),
        
        "TWITTER_IMAGE":
            "https://s3.amazonaws.com/s3.boldprogressives.org/images/"
            "OpenDebates_VOTE-NOW_TW-1024x512-FODUrl.png",
        "TWITTER_SITE_TEXT":
            u"VOTE & submit questions for #FLSen #OpenDebate between @DavidJollyFL & "
            u"@AlanGrayson h/t @OpenDebates @ProgChangeInst",
        "TWITTER_SITE_TITLE":
            u"U.S. Senate candidates answer YOUR questions!",
        "TWITTER_SITE_DESCRIPTION":
            u"Voters set the agenda for groundbreaking #OpenDebate. Tune in Mon 4/25 @7pm EDT "
            u"on TYTNetwork.com. Submit & vote here!",
        "TWITTER_QUESTION_TEXT":
            u"VOTE & submit questions for #FLSen #OpenDebate between @DavidJollyFL & @AlanGrayson "
            u"h/t @OpenDebates @ProgChangeInst",
        "TWITTER_QUESTION_TITLE":
            u"Vote on this question for the FL-Sen #OpenDebate!",
        "TWITTER_QUESTION_DESCRIPTION":
            u'"{idea}" Debate is 4/25 at 7pm EDT on TYTNetwork.com.',

        "FACEBOOK_IMAGE":
            "https://s3.amazonaws.com/s3.boldprogressives.org/images/"
            "OpenDebates_VOTE-NOW_FB-1200x717-FODUrl.png",
        "FACEBOOK_SITE_TITLE":
            u"HISTORIC: Florida U.S. Senate Candidates answer YOUR top-voted questions!",
        "FACEBOOK_SITE_DESCRIPTION":
            u"All questions for groundbreaking #OpenDebate on Mon 4/25 @7pm EDT on TYTNetwork.com "
            u"will be chosen from top vote-getters online. Hosted by Open Debate Coalition",
        "FACEBOOK_QUESTION_TITLE":
            u'Click to vote on this question for Senate candidates to answer at the #OpenDebate '
            u'in Florida!',
        "FACEBOOK_QUESTION_DESCRIPTION":
            u'"{idea}" Mon, 4/25 @7pm EDT on TYTNetwork.com, Jolly & Grayson answer YOUR '
            u'questions!',

        "EMAIL_SUBJECT":
            "Help me set the agenda for the debate between Alan Grayson and David Jolly!",
        "EMAIL_BODY":
            dedent("""
            Hi there!

            I just participated in a first-of-its-kind Open Debate for U.S. Senate candidates in
            Florida where all questions will be chosen from among the Top 30 voted on by the
            public online.

            Could you vote on this question so David Jolly and Alan Grayson can answer it live at
            the debate?

            %(url)s

            There are tons of other great questions to vote on at FloridaOpenDebate.com. You can
            search by topic area or keyword, or you can even submit your own question. Voting
            closes just before the debate begins at 7:00 pm EDT on Monday, April 25. Tune in to
            FloridaOpenDebate.com to watch this event, co-hosted by the Open Debate Coalition and
            the Progressive Change Institute.

            Thanks for helping us create a debate for U.S. Senate that reflects the real concerns
            of Americans!"""),
    },
    'testing': {  # Presidential Debate
        "HASHTAG": "DemOpenForum",
        "HEADER_TITLE": _("WELCOME TO THE\nDEMOCRATIC OPEN FORUM"),
        "HEADER_COPY": _(
            u"Ask Bernie Sanders and Hillary Clinton about the issues that are most important "
            "to you -- then vote and tell others! Watch the Democratic Open Forum on CNN "
            "or right here on Monday, April 25, at 8:00 pm EDT. All questions will be chosen from "
            "among those that receive the most votes online."),

        "AFTER_QUESTION_SUBMITTED_TEXT": _(
            u"Next, help your question collect votes. Share it on social media "
            u"and email it to friends. The Top 30 questions with the most votes "
            u"will be shared with debate moderators."),
        
        # FIXME: Twitter & Facebook settings for Presidential debate
        "TWITTER_IMAGE":
            "https://s3.amazonaws.com/s3.boldprogressives.org/images/"
            "OpenDebates_VOTE-NOW_TW-1024x512-FODUrl.png",
        "TWITTER_SITE_TEXT":
            u"Submit & vote on questions for FL-Sen #OpenDebate between @DavidJollyFL "
            "& @AlanGrayson hosted by Open Debate Coalition, Progressive Change Inst.",
        "TWITTER_SITE_TITLE":
            u"U.S. Senate candidates answer YOUR questions!",
        "TWITTER_SITE_DESCRIPTION":
            u"Mon 4/25 @8pm EDT on [TBD]: Voters set the agenda for groundbreaking #OpenDebate. "
            "Submit & vote here!",
        "TWITTER_QUESTION_TEXT":
            u"Submit & vote on questions for FL-Sen #OpenDebate between @DavidJollyFL "
            "& @AlanGrayson hosted by Open Debate Coalition, Progressive Change Inst.",
        "TWITTER_QUESTION_TITLE":
            u"Click here to vote on this question for U.S. Senate candidates to answer at "
            "the #OpenDebate in Florida!",
        "TWITTER_QUESTION_DESCRIPTION":
            u'"{idea}" At 8pm EDT on 4/25, Jolly & Grayson answer top vote-getting questions '
            'at bottom-up #OpenDebate hosted by [TBD], Open Debate Coalition, '
            'Progressive Change Institute',

        "FACEBOOK_IMAGE":
            "https://s3.amazonaws.com/s3.boldprogressives.org/images/"
            "OpenDebates_VOTE-NOW_FB-1200x717-FODUrl.png",
        "FACEBOOK_SITE_TITLE":
            u"HISTORIC: Florida U.S. Senate Candidates answer YOUR top-voted questions!",
        "FACEBOOK_SITE_DESCRIPTION":
            u"Groundbreaking bottom-up #OpenDebate to take place Mon 4/25 @7pm EDT, hosted "
            "by Open Debate Coalition, Progressive Change Institute, & [MEDIA PARTNER]. All "
            "questions will be chosen from top vote-getters online. Submit & vote here!",
        "FACEBOOK_QUESTION_TITLE":
            u'Click here to vote on this question for U.S. Senate candidates to answer at the '
            '#OpenDebate in Florida!',
        "FACEBOOK_QUESTION_DESCRIPTION":
            u'"{idea}" At 8pm EDT on 4/25, Jolly & Grayson answer top vote-getting questions '
            'at bottom-up #OpenDebate hosted by [TBD], Open Debate Coalition, Progressive '
            'Change Institute',

        "EMAIL_SUBJECT": "Vote for my progressive idea for @OpenDebaters",
        "EMAIL_BODY": "Vote for my progressive idea for @OpenDebaters %(url)s",
    },
}
SITE_THEME_NAME = 'florida'
SITE_THEME = SITE_THEMES[SITE_THEME_NAME]
# SITE_THEME_NAME and SITE_THEME get overriden in local_settings

# SECRET_KEY is overriden in deploy settings
SECRET_KEY = 'secret-key-for-local-use-only'

TEST = 'test' in sys.argv
if TEST:
    # https://docs.djangoproject.com/en/1.8/topics/testing/overview/#other-test-conditions
    # DEBUG is False for tests no matter what we set, so set it up properly for
    # use later in this file
    DEBUG = False
else:
    DEBUG = 'DJANGO_DEBUG' in os.environ

ALLOWED_HOSTS = []

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
    'djorm_pgfulltext',
    'endless_pagination',
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

PIPELINE_COMPILERS = (
    'pipeline.compilers.less.LessCompiler',
)

if DEBUG:
    PIPELINE_CSS_COMPRESSOR = None
    PIPELINE_JS_COMPRESSOR = None

if TEST:
    PIPELINE_COMPILERS = ()
    PIPELINE_ENABLED = False

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
for theme in SITE_THEMES:
    PIPELINE_CSS['theme-%s' % (theme,)] = {
        'source_filenames': (
            'less/theme-%s.less' % (theme,),
        ),
        'output_filename': 'css/theme-%s.css' % (theme,),
        'extra_context': {
            'media': 'screen,projection',
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
    'registration': {
        'source_filenames': (
            'js/registration.js',
        ),
        'output_filename': 'js/registration.js',
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

LOGIN_REDIRECT_URL = '/'
