from base import *
from datetime import timedelta

import requests

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'kmscrypt::AQICAHhyudebozg2Jnr8hMO6X7V8HDceBAM0mD5BC9ALYbbZCAG1m3vfJ0osy95vvriR7HYXAAAAkjCBjwYJKoZIhvcNAQcGoIGBMH8CAQAwegYJKoZIhvcNAQcBMB4GCWCGSAFlAwQBLjARBAw50YonaU5UR0gzRoECARCATezWtfA7leaFNNhRcUQN/+mcAkDQDMEu+x06h/fy+jxvZiM+7neTXyKKwzxTWQ5iwJwo1WXgOIN6P+CEqIrxBpRJ9nYg4F9RLTViv4JL'
JWT_SECRET = '5xPH5VVMUyvx_eNavZzJwV4vo75rpN3Idk3HeUeWxCDjeiDg2n5ECOJROiBbtLja'
SYSTEM_AUTH_TOKEN = 'Elz7dGCS82QjzO3kdaPRd3gZjgQgRPcmoKcLTcphiOIVwH4LOa03GFz7yMRb'

# Use 1/x of the truven data for traditional plan analysis
#TRUVEN_FRACTION = os.environ.get('TRUVEN_FRACTION', '1000')
#ADJUDICATION_TABLE = 'z08_leslie.adjudication_table'

# append the expected domain name the service will be accessed at.
# for shared environment we'll use a wild card since there are so many environments this config will be used for
ALLOWED_HOSTS.append(".dev-bind.com")
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
