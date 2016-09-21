from opendebates.utils import get_site_mode


class SiteModeMiddleware(object):
    """
    Gets or creates a SiteMode for the request, based on the hostname.
    """

    def process_view(self, request, view_func, view_args, view_kwargs):
        request.site_mode = get_site_mode(request)
