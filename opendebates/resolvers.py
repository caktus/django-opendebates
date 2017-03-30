from importlib import import_module

from django.conf.urls import url, include


class PrefixedUrlconf(object):
    def __init__(self, prefix):
        self.prefix = prefix

    @property
    def urlpatterns(self):
        url_module = import_module('opendebates.urls')

        return [
            pattern
            if (
                not hasattr(pattern, 'urlconf_name') or
                getattr(pattern.urlconf_name, '__name__', None) != 'opendebates.prefixed_urls'
            ) else
            url(r'^{}/'.format(self.prefix), include('opendebates.prefixed_urls'))
            for pattern in url_module.urlpatterns
        ]
