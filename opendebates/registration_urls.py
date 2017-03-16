"""
URLconf for registration and activation, using django-registration's
one-step backend.

If the default behavior of these views is acceptable to you, simply
use a line like this in your root URLconf to set up the default URLs
for registration::

    (r'^accounts/', include('registration.backends.simple.urls')),

This will also automatically set up the views in
``django.contrib.auth`` at sensible default locations.

If you'd like to customize registration behavior, feel free to set up
your own URL patterns for these views instead.

"""


from django.conf.urls import include
from django.conf.urls import patterns
from django.conf.urls import url
from django.contrib.auth import views as auth_views

from .forms import OpenDebatesAuthenticationForm
from .views import OpenDebatesRegistrationView, od_logout

urlpatterns = patterns('',
                       url(r'^register/$',
                           OpenDebatesRegistrationView.as_view(),
                           name='registration_register'),
                       # url(r'^register/closed/$',
                       #     TemplateView.as_view(template_name='registration/registration_closed.html'),
                       #     name='registration_disallowed'),
                       url(r'^register/complete/$',
                           'opendebates.views.registration_complete', name="registration_complete"),
                       url(r'^login/$',
                           'django.contrib.auth.views.login',
                           {
                               'template_name': 'registration/login.html',
                               'authentication_form': OpenDebatesAuthenticationForm,
                           },
                           name='auth_login'),

                       # override the default urls
                       url(r'^password/change/$',
                           auth_views.password_change,
                           name='password_change'),
                       url(r'^password/change/done/$',
                           auth_views.password_change_done,
                           name='password_change_done'),
                       url(r'^password/reset/$',
                           auth_views.password_reset,
                           {'html_email_template_name': "registration/password_reset_email.html",
                            'email_template_name': "registration/password_reset_email.txt",
                            'template_name': "registration/password_reset_form.html"},
                           name='password_reset'),
                       url(r'^password/reset/done/$',
                           auth_views.password_reset_done,
                           name='password_reset_done'),
                       url(r'^password/reset/complete/$',
                           auth_views.password_reset_complete,
                           name='password_reset_complete'),
                       url(r'^password/reset/confirm/(?P<uidb64>[0-9A-Za-z]+)-(?P<token>.+)/$',
                           auth_views.password_reset_confirm,
                           name='password_reset_confirm'),
                       url(r'^logout/$',
                           od_logout,
                           {'template_name': 'registration/logout.html',
                            'next_page': "list_ideas"}),

                       (r'', include('registration.auth_urls')),
                       )
