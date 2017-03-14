from opendebates.utils import get_site_mode


class SiteModeMiddleware(object):
    """
    Gets or creates a SiteMode for the request, based on the hostname.
    """

    def process_request(self, request):
        request.site_mode = get_site_mode(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        if 'prefix' in view_kwargs:
            prefix = view_kwargs.pop('prefix')
            if not getattr(request, 'site_mode', None):
                request.site_mode = get_site_mode(request)
