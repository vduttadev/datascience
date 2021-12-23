from base import *
from datetime import timedelta

import requests

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'kmscrypt::AQECAHiyAh7vHgaEt6qQEX+SFe8fOUeP89ZxtBnnj2QRl7LS5AAAAJIwgY8GCSqGSIb3DQEHBqCBgTB/AgEAMHoGCSqGSIb3DQEHATAeBglghkgBZQMEAS4wEQQMf6/Eho7bm3uqn7u/AgEQgE22BRruqSHL9hdGXMxrxIv3/rPyXKukHd70i8/42NgDi3YXPDjTput423CR1dUlCUnIIUITht0BduG7d8zzevxBoDhBwvx1ivERqrv4JQ=='
JWT_SECRET = 'kmscrypt::AQECAHiyAh7vHgaEt6qQEX+SFe8fOUeP89ZxtBnnj2QRl7LS5AAAAKIwgZ8GCSqGSIb3DQEHBqCBkTCBjgIBADCBiAYJKoZIhvcNAQcBMB4GCWCGSAFlAwQBLjARBAxGfT/04E4YEfcRsqgCARCAW1mttxr8H9RhTAa7Pb/Eg8EosDSkE4lHItbdd/0H1W7Q4/Et0ey0eNuEth/4BAUPuoMQRsswZBmkZi3zud08JDE8Fjx4GhbMsOlhQZy7gNyPWeetH0txttvLWc0='
SYSTEM_AUTH_TOKEN = 'kmscrypt::AQECAHiyAh7vHgaEt6qQEX+SFe8fOUeP89ZxtBnnj2QRl7LS5AAAAJ4wgZsGCSqGSIb3DQEHBqCBjTCBigIBADCBhAYJKoZIhvcNAQcBMB4GCWCGSAFlAwQBLjARBAwnnrRGZGg8hq6t7F0CARCAV7ODw+03H6WMfHb0JIYdXPH+bnY2lZilYOYW8YEigv+CVCF03u2/DILcodtt4ztp7v6PfWYgepnG6xnUKZb+TNqR4Q4UBPd7Q7Dd5oCtkela8uKBI6fuuw=='

# Use 1/x of the truven data for traditional plan analysis
#TRUVEN_FRACTION = os.environ.get('TRUVEN_FRACTION', '1000')
#ADJUDICATION_TABLE = 'z08_leslie.adjudication_table'


# append the expected domain name the service will be accessed at
ALLOWED_HOSTS.append("services-stage.dev-bind.com")
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
