from django.http import Http404

from opendebates.utils import get_site_mode


class SiteModeMiddleware(object):
    """
    Gets or creates a SiteMode for the request, based on the hostname.
    """

    def process_request(self, request):
        request.site_mode = get_site_mode(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        if 'prefix' in view_kwargs:
            view_kwargs.pop('prefix')
            if not getattr(request, 'site_mode', None):
                request.site_mode = get_site_mode(request)
                if request.site_mode is None:
                    # Make sure to fall back in this case, so that the
                    # flatpage middleware will get its shot.
                    raise Http404
