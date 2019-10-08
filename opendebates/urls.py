from django.conf.urls import include, url
from django.contrib import admin


urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
    url(r'^healthcheck.html$', 'opendebates.views.health_check', name='health_check'),
    url(r'^(?P<prefix>[-\w]+)/', include('opendebates.prefixed_urls')),
    url(r'', include('opendebates.prefixed_urls')),  # Can use this by hostname?
]
