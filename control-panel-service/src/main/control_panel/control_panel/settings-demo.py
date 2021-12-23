from base import *
from datetime import timedelta

import requests

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 's7%-^hxkv)q_1&(hx7-8epo)68hzl9!-)@k+&6levfiv!%#m(n'
JWT_SECRET = 'kmscrypt::AQICAHg/w+uPdbbFQ/9st3B08gSQs2EeJBldI1qoLr+t/OrZ/gGgIE3YGfUbn/J4YM1MXTK0AAAAojCBnwYJKoZIhvcNAQcGoIGRMIGOAgEAMIGIBgkqhkiG9w0BBwEwHgYJYIZIAWUDBAEuMBEEDObozRPDf0rU5E54GAIBEIBbUOvK4o0DXCYbKTi5kujOgBjSS9z/JBBOgYI4yrFBlG7P8UYEgCfz+2Rv+FiRHl9AH0mzADpsj6uZ7gIPA1To1+gPXOAqzEjC+aSe6hcRVUAzfVGnWsgkSsJO8A=='


# Use 1/x of the truven data for traditional plan analysis
#TRUVEN_FRACTION = os.environ.get('TRUVEN_FRACTION', '1000')
#ADJUDICATION_TABLE = 'z08_leslie.adjudication_table'

# append the expected domain name the service will be accessed at
ALLOWED_HOSTS.append("services-daisy.yourbind.com")
# append the local ip address for the ALB health check to use.
try:
    ALLOWED_HOSTS.append(requests.get(
        'http://169.254.169.254/latest/meta-data/local-ipv4').text)
except requests.exceptions.RequestException:
    pass

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(seconds=1200),
    'REFRESH_TOKEN_LIFETIME': timedelta(seconds=2400),

    'ALGORITHM': 'HS256',
    'SIGNING_KEY': JWT_SECRET,
    'VERIFYING_KEY': JWT_SECRET,

    'AUTH_HEADER_TYPES': ('Bearer', '',),

    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',

    'JTI_CLAIM': 'jti',
}
