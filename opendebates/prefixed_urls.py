from django.conf.urls import include, url

from opendebates import views, moderator_views

urlpatterns = [
    url(r'^$', views.list_ideas, name="list_ideas"),
    url(r'^changelog/$', views.changelog, name='changelog'),

    url(r'^recent/$', views.recent_activity, name='recent_activity'),
    url(r'^questions/(?P<id>\d+)/vote/$', views.vote, name="vote"),
    url(r'^questions/(?P<id>\d+)/$', views.vote, name="show_idea"),
    url(r'^questions/(?P<id>\d+)/report/$', views.report, name='report'),
    url(r'^questions/(?P<id>\d+)/merge/$', views.merge, name='merge'),

    url(r'^top/(?P<slug>[-\w]+)/$', views.top_archive, name='top_archive'),

    url(r'^category/(?P<cat_id>\d+)/$', views.list_category, name="list_category"),
    url(r'^category/(?P<cat_id>\d+)/search/$', views.category_search, name="category_search"),
    url(r'^search/$', views.search_ideas, name="search_ideas"),
    url(r'^questions/$', views.questions, name="questions"),
    # url(r'^candidates/$', views.list_candidates', name="candidates"),

    url(r'^moderation/remove/$', moderator_views.remove, name="moderation_remove"),
    url(r'^moderation/merge/$', moderator_views.merge, name="moderation_merge"),
    url(r'^moderation/$', moderator_views.home, name='moderation_home'),
    url(r'^moderation/preview/$', moderator_views.preview, name="moderation_preview"),
    url(r'^moderation/top/$', moderator_views.add_to_top_archive, name="moderation_add_to_top_archive"),

    url(r'^registration/', include('opendebates.registration_urls')),
]
