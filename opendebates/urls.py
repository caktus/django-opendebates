from django.conf.urls import include, url


urlpatterns = [
    url(r'^(?P<prefix>[-\w]+)/', include('opendebates.prefixed_urls')),
    url(r'^', include('opendebates.unprefixed_urls')),
]
