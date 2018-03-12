import logging
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.conf import settings
from django.utils import timezone

log = logging.getLogger('reportek.auth')
info = log.info
debug = log.debug
warn = log.warning
error = log.error


class ExpiringTokenAuthentication(TokenAuthentication):
    """
    Authentication backend for expiring tokens
    """
    def authenticate_credentials(self, key):
        model = self.get_model()
        try:
            token = model.objects.get(key=key)
        except model.DoesNotExist:
            debug(f'Token {key} auth failed: invalid token')
            raise AuthenticationFailed('Invalid token')

        if not token.user.is_active:
            debug(f'Token {key} auth failed for "{token.user}": user inactive')
            raise AuthenticationFailed('User inactive or deleted')

        if token.created < timezone.now() - settings.TOKEN_EXPIRE_INTERVAL:
            debug(f'Token {key} auth failed for "{token.user}": expired token')
            raise AuthenticationFailed('Token has expired')

        debug(f'Successful token auth for "{token.user}": {key}')
        return token.user, token
