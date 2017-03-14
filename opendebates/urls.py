from django.conf.urls import include, url
from django.contrib import admin

urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
    url(r'^healthcheck.html$', 'opendebates.views.health_check', name='health_check'),

    url(r'^(?P<prefix>[-\w]+)/$', 'opendebates.views.list_ideas', name="list_ideas"),
    url(r'^(?P<prefix>[-\w]+)/changelog/$', 'opendebates.views.changelog', name='changelog'),
    # url(r'^(?P<prefix>[-\w]+)/test/$', 'opendebates.views.test', name='test'),

    url(r'^(?P<prefix>[-\w]+)/recent/$', 'opendebates.views.recent_activity',
        name='recent_activity'),
    url(r'^(?P<prefix>[-\w]+)/questions/(?P<id>\d+)/vote/$', 'opendebates.views.vote', name="vote"),
    # url(r'^(?P<prefix>[-\w]+)/comment/$', 'opendebates_comments.views.post_comment',
    #     name="comment"),
    url(r'^(?P<prefix>[-\w]+)/questions/(?P<id>\d+)/$', 'opendebates.views.vote', name="show_idea"),
    url(r'^(?P<prefix>[-\w]+)/questions/(?P<id>\d+)/report/$', 'opendebates.views.report',
        name='report'),
    url(r'^(?P<prefix>[-\w]+)/questions/(?P<id>\d+)/merge/$', 'opendebates.views.merge',
        name='merge'),

    url(r'^(?P<prefix>[-\w]+)/top/(?P<slug>[-\w]+)/$', 'opendebates.views.top_archive',
        name='top_archive'),

    url(r'^(?P<prefix>[-\w]+)/category/(?P<cat_id>\d+)/$', 'opendebates.views.list_category',
        name="list_category"),
    url(r'^(?P<prefix>[-\w]+)/category/(?P<cat_id>\d+)/search/$', 'opendebates.views.category_search',
        name="category_search"),
    url(r'^(?P<prefix>[-\w]+)/search/$', 'opendebates.views.search_ideas', name="search_ideas"),
    url(r'^(?P<prefix>[-\w]+)/questions/$', 'opendebates.views.questions', name="questions"),
    # url(r'^(?P<prefix>[-\w]+)/candidates/$', 'opendebates.views.list_candidates', name="candidates"),

    url(r'^(?P<prefix>[-\w]+)/moderation/remove/$', 'opendebates.moderator_views.remove',
        name="moderation_remove"),
    url(r'^(?P<prefix>[-\w]+)/moderation/merge/$', 'opendebates.moderator_views.merge',
        name="moderation_merge"),
    url(r'^(?P<prefix>[-\w]+)/moderation/$', 'opendebates.moderator_views.home',
        name='moderation_home'),
    url(r'^(?P<prefix>[-\w]+)/moderation/preview/$', 'opendebates.moderator_views.preview',
        name="moderation_preview"),
    url(r'^(?P<prefix>[-\w]+)/moderation/top/$', 'opendebates.moderator_views.add_to_top_archive',
        name="moderation_add_to_top_archive"),

    url(r'^(?P<prefix>[-\w]+)/registration/', include('opendebates.registration_urls')),
]
