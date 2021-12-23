from django.utils.translation import ugettext_lazy as _
from rest_framework_simplejwt import authentication
from rest_framework_simplejwt.exceptions import AuthenticationFailed
from django.conf import settings


import logging


logger = logging.getLogger('control_panel')


class JWTTokenUserAuthenticationExt(authentication.JWTAuthentication):

    """
    An authentication plugin that authenticates requests through a JSON web
    token provided in a request header.
    """

    """
    Extracts the header containing the JSON web token from the given
    request.
    """

    def get_header_data(self, request):
        logger.info('request=api command=getHeaderToken')
        header = request.META.get('HTTP_SYSTEM_AUTHORIZATION')
        logger.debug('request=api valid_token header=%s' % (header))
        return header

    def authenticate(self, request):
        logger.info('request=api command=authenticate')
        raw_token = self.get_header_data(request)
        logger.debug('request=api raw_token=%s' % (raw_token))
        if raw_token is None:
            logger.info('request=api token=None detail=Authentication failure - No token passed')
            raise AuthenticationFailed(
                _('Authorization header must contain token in System-Authorization'),
                code='bad_authorization_header',
            )
        validated_token = self.get_validated_token(raw_token)

        logger.debug('request=api token=%s valid_token=%s' % (raw_token, validated_token))
        if validated_token == 'valid':
            logger.info('request=api description=Token valid caller=System')
            return None
        else:
            logger.debug('request=api token=%s detail=Authentication failure' % (validated_token))
            raise AuthenticationFailed(
                _('Invalid System-Authorization token'),
                code='invalid_authorization_token',
            )

    def get_validated_token(self, raw_token):
        """
        Validates an encoded JSON web token and returns a validated token
        wrapper object.
        """
        logger.debug('request=api valid_token2 raw_token=%s and ref_token=%s' %
                     (raw_token, settings.SYSTEM_AUTH_TOKEN))

        if raw_token == settings.SYSTEM_AUTH_TOKEN:
            logger.info('request=api desciption=valid token')
            return 'valid'
        else:
            logger.info('request=api desciption=Invalid token for system call')
            return 'invalid'
