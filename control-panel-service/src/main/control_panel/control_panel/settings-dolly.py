from base import *
from datetime import timedelta
import requests

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 's7%-^hxkv)q_1&(hx7-8epo)68hzl9!-)@k+&6levfiv!%#m(n'
JWT_SECRET = 'kmscrypt::AQICAHi8QtJppwqqHo5RWgKdEdd0eg8s3GPKwzizo+LCTy1UNgElGM2neXJae+5Dbhpl0yfsAAAAojCBnwYJKoZIhvcNAQcGoIGRMIGOAgEAMIGIBgkqhkiG9w0BBwEwHgYJYIZIAWUDBAEuMBEEDCSl0ZO3GXHHYJN3CQIBEIBbghQiOgrbANSXNpXVhKYX+4XJOmzKQ4eUiusDo9kyYkTatQDClkXQqPMPz2vh0FslZIyjK81MN/5PqXin9p2I27H7PdcmrqtP9r5DP9889nrVteLvec1XOINZnw=='
SYSTEM_AUTH_TOKEN = 'kmscrypt::AQICAHi8QtJppwqqHo5RWgKdEdd0eg8s3GPKwzizo+LCTy1UNgHaDBO/oaH104XrRpAfv+DyAAAAojCBnwYJKoZIhvcNAQcGoIGRMIGOAgEAMIGIBgkqhkiG9w0BBwEwHgYJYIZIAWUDBAEuMBEEDNzbeCEYo83sPlC/iAIBEIBbQGpfLUqAeiCvbKlCuHtmXoGPju0x7KC/6q6IpEl31VurEvf8jq9M8o1GLj1S6DGdH6YfCvUxUJUdomuRiEFKyE6pIWCaqjf1Q7JYyYnktjvq6gOEO3rxblk7wA=='

# Use 1/x of the truven data for traditional plan analysis
#TRUVEN_FRACTION = os.environ.get('TRUVEN_FRACTION', '1000')
#ADJUDICATION_TABLE = 'z08_leslie.adjudication_table'


# append the expected domain name the service will be accessed at
ALLOWED_HOSTS.append("services-dolly.yourbind.com")
# append the local ip address for the ALB health check to use.
try:
    ALLOWED_HOSTS.append(requests.get('http://169.254.169.254/latest/meta-data/local-ipv4').text)
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
