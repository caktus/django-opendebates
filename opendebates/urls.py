from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin

from opendebates import views

urlpatterns = [
    url(r'^$', views.root_redirect),
    url(r'^admin/', admin.site.urls),
    url(r'^healthcheck.html$', views.health_check, name='health_check'),
    url(r'^(?P<prefix>[-\w]+)/', include('opendebates.prefixed_urls')),
]


if settings.DEBUG:
    import debug_toolbar

    urlpatterns += [
        url('__debug__/', include(debug_toolbar.urls)),
    ]
