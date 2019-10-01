from django.http import Http404
from django.utils.deprecation import MiddlewareMixin

from opendebates.resolvers import PrefixedUrlconf
from opendebates.utils import get_debate


class DebateMiddleware(MiddlewareMixin, object):
    """
    Gets a Debate for the request, based on the hostname.
    """

    def process_request(self, request):
        request.debate = get_debate(request)
        if request.debate:
            request.urlconf = PrefixedUrlconf(request.debate.prefix)

    def process_view(self, request, view_func, view_args, view_kwargs):
        if 'prefix' in view_kwargs:
            view_kwargs.pop('prefix')
            if not getattr(request, 'debate', None):
                request.debate = get_debate(request)
                if request.debate is None:
                    # Make sure to fall back in this case, so that the
                    # flatpage middleware will get its shot.
                    raise Http404
