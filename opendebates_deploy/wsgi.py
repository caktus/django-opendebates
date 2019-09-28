"""
WSGI config for opendebates project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/howto/deployment/wsgi/
"""

import os


# Make sure settings module is set BEFORE get_wsgi application and also
# that we process settings before importing DjangoWhiteNoise...
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "opendebates.settings")

from django.core.wsgi import get_wsgi_application  # noqa
application = get_wsgi_application()

from whitenoise.django import DjangoWhiteNoise  # noqa
application = DjangoWhiteNoise(application)
