from base import *
from datetime import timedelta


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 's7%-^hxkv)q_1&(hx7-8epo)68hzl9!-)@k+&6levfiv!%#m(n'
JWT_SECRET = '5xPH5VVMUyvx_eNavZzJwV4vo75rpN3Idk3HeUeWxCDjeiDg2n5ECOJROiBbtLja'
SYSTEM_AUTH_TOKEN = 'Elz7dGCS82QjzO3kdaPRd3gZjgQgRPcmoKcLTcphiOIVwH4LOa03GFz7yMRb'


ALLOWED_HOSTS = ['0.0.0.0', '127.0.0.1', 'localhost']

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
