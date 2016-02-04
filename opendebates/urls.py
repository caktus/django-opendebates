from django.conf.urls import include, url
from django.contrib import admin

urlpatterns = [
    url('^$', 'opendebates.views.list_ideas', name="list_ideas"),
    url(r'^healthcheck.html$', 'opendebates.views.health_check', name='health_check'),
    url(r'^test/$', 'opendebates.views.test', name='test'),

    url(r'^recent/$', 'opendebates.views.recent_activity', name='recent_activity'),
    url('^questions/(?P<id>\d+)/vote/$', 'opendebates.views.vote', name="vote"),
    url('^comment/$', 'opendebates_comments.views.post_comment',
        name="comment"),
    url('^questions/(?P<id>\d+)/$', 'opendebates.views.vote', name="show_idea"),

    url('^category/(?P<cat_id>\d+)/$', 'opendebates.views.list_category', name="list_category"),
    url('^category/(?P<cat_id>\d+)/search/$', 'opendebates.views.category_search',
        name="category_search"),
    url('^search/$', 'opendebates.views.search_ideas', name="search_ideas"),
    url('^questions/$', 'opendebates.views.questions', name="questions"),
    url('^candidates/$', 'opendebates.views.list_candidates', name="candidates"),

    url('^moderation/mark_duplicate/$', 'opendebates.moderator_views.mark_duplicate',
        name="moderation_mark_duplicate"),

    url(r'^admin/', include(admin.site.urls)),
    url(r'^registration/', include('opendebates.registration_urls')),
]
