from opendebates.utils import get_site_mode


class SiteModeMiddleware(object):
    """
    Gets or creates a SiteMode for the request, based on the hostname.
    """

    def process_request(self, request):
        request.site_mode = get_site_mode(request)
