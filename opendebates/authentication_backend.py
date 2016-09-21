from django.contrib.auth import get_user_model


class EmailAuthBackend(object):
    """
    Email Authentication Backend

    Allows a user to sign in using an email/password pair rather than
    a username/password pair.
    """

    def authenticate(self, username=None, password=None, request=None):
        """ Authenticate a user based on email address as the user name. """
        User = get_user_model()
        try:
            # when logging in via email address, only authenticate users
            # on the current site
            user = User.objects.get(email=username, voter__site_mode=request.site_mode)
            if user.check_password(password):
                return user
        except Exception:
            return None

    def get_user(self, user_id):
        """ Get a User object from the user_id. """
        User = get_user_model()
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
