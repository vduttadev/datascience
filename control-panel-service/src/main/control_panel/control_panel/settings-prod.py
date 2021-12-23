from base import *
from datetime import timedelta

import requests

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = ''  # Prod secret key(kmscrypt::xxxxxxx) to be added by DEVOPS
JWT_SECRET = 'kmscrypt::AQECAHjDYzFxP97qnfqUKq1Al8VteYgIgtQRvYCIax3qiwyQxQAAAKIwgZ8GCSqGSIb3DQEHBqCBkTCBjgIBADCBiAYJKoZIhvcNAQcBMB4GCWCGSAFlAwQBLjARBAxeFb8wK0XSedx0X8QCARCAW99u+y1qrIXDXWRMFmufjhCPb4mPi+Zk4K8T3xS2hHNnFoG5UeGlapiE+72d5vhtk9wCnNsPy70TA8xOMaP5741bP3CXZFrbqZ3o5SSdPU9uANKUJ6P8lVIlxgU='
SYSTEM_AUTH_TOKEN = 'kmscrypt::AQECAHjDYzFxP97qnfqUKq1Al8VteYgIgtQRvYCIax3qiwyQxQAAAJ4wgZsGCSqGSIb3DQEHBqCBjTCBigIBADCBhAYJKoZIhvcNAQcBMB4GCWCGSAFlAwQBLjARBAxID6Hw+m636SfWGV8CARCAV9BV6dDCOYew1albasvqM3MeLiq5wf/XzclxNxR0l95Vgb5QNvGUWHBoSjgpdDT4zgGt2UWy2awH8n1HG7UmVtC/QrOBt7mRIOvneH/9Ov8tvVnX6xTyeA=='

# Use 1/x of the truven data for traditional plan analysis
#TRUVEN_FRACTION = os.environ.get('TRUVEN_FRACTION', '1000')
#ADJUDICATION_TABLE = 'z08_leslie.adjudication_table'


# append the expected domain name the service will be accessed at
ALLOWED_HOSTS.append("services-prod.yourbind.com")
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
