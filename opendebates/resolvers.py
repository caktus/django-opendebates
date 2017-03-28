from importlib import import_module

from django.conf.urls import url, include
from django.core.urlresolvers import RegexURLResolver


class PrefixedUrlconf(object):
    def __init__(self, prefix):
        self.prefix = prefix

    @property
    def urlpatterns(self):
        url_module = import_module('opendebates.urls')

        return [
            url_resolver
            if url_resolver.urlconf_name.__name__ != 'opendebates.prefixed_urls' else
            url(r'^{}/'.format(self.prefix), include('opendebates.prefixed_urls'))
            for url_resolver in url_module.urlpatterns
        ]
