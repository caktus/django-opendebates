from django.conf.urls import include, url


urlpatterns = [
    url(r'^$', 'opendebates.views.list_ideas', name="list_ideas"),
    url(r'^changelog/$', 'opendebates.views.changelog', name='changelog'),

    url(r'^recent/$', 'opendebates.views.recent_activity',
        name='recent_activity'),
    url(r'^questions/(?P<id>\d+)/vote/$', 'opendebates.views.vote', name="vote"),
    # url(r'^comment/$', 'opendebates_comments.views.post_comment',
    #     name="comment"),
    url(r'^questions/(?P<id>\d+)/$', 'opendebates.views.vote', name="show_idea"),
    url(r'^questions/(?P<id>\d+)/report/$', 'opendebates.views.report',
        name='report'),
    url(r'^questions/(?P<id>\d+)/merge/$', 'opendebates.views.merge',
        name='merge'),

    url(r'^top/(?P<slug>[-\w]+)/$', 'opendebates.views.top_archive',
        name='top_archive'),

    url(r'^category/(?P<cat_id>\d+)/$', 'opendebates.views.list_category',
        name="list_category"),
    url(r'^category/(?P<cat_id>\d+)/search/$',
        'opendebates.views.category_search', name="category_search"),
    url(r'^search/$', 'opendebates.views.search_ideas', name="search_ideas"),
    url(r'^questions/$', 'opendebates.views.questions', name="questions"),
    # url(r'^candidates/$',
    #     'opendebates.views.list_candidates', name="candidates"),

    url(r'^moderation/remove/$', 'opendebates.moderator_views.remove',
        name="moderation_remove"),
    url(r'^moderation/merge/$', 'opendebates.moderator_views.merge',
        name="moderation_merge"),
    url(r'^moderation/$', 'opendebates.moderator_views.home',
        name='moderation_home'),
    url(r'^moderation/preview/$', 'opendebates.moderator_views.preview',
        name="moderation_preview"),
    url(r'^moderation/top/$', 'opendebates.moderator_views.add_to_top_archive',
        name="moderation_add_to_top_archive"),

    url(r'^registration/', include('opendebates.registration_urls')),
]
