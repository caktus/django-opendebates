from django.conf import settings
from django.templatetags import cache as cache_tag

from mock import patch


class FakeNeverExpiringCacheNode(cache_tag.CacheNode):
    def __init__(self, nodelist, expire_time_var, fragment_name, vary_on, cache_name):
        self.nodelist = nodelist
        self.expire_time_var = expire_time_var
        self.fragment_name = fragment_name
        self.vary_on = vary_on
        self.cache_name = cache_name
        self.fake_cache = {}

    def render(self, context):
        vary_on = [var.resolve(context) for var in self.vary_on]
        cache_key = cache_tag.make_template_fragment_key(self.fragment_name, vary_on)

        value = self.fake_cache.get(cache_key)
        if value is None:
            value = self.nodelist.render(context)
            self.fake_cache[cache_key] = value
        return value


def patch_cache_templatetag():
    return patch.object(cache_tag, 'CacheNode', FakeNeverExpiringCacheNode)


def reset_session(client):
    del client.cookies[settings.SESSION_COOKIE_NAME]
    client.session
