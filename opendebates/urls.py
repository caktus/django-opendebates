from django.conf.urls import include, url
from django.contrib import admin


urlpatterns = [
    url(r'^(?P<prefix>[-\w]+)/', include('opendebates.prefixed_urls'), {'prefix': 'foo'}),
    url(r'^', include('opendebates.unprefixed_urls')),
]
