from functools import wraps

from django.contrib.auth import REDIRECT_FIELD_NAME
from django.core.urlresolvers import reverse


def od_login_required(f):
    @wraps(f)
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated():
            return f(request, *args, **kwargs)

        path = request.get_full_path()
        resolved_login_url = reverse('auth_login', kwargs={'prefix': request.site_mode.prefix})
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(
            path, resolved_login_url, REDIRECT_FIELD_NAME)
    return wrapper
