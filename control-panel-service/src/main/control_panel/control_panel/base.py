import os
import yaml
from socket import gethostname, gethostbyname

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# setup default ALLOWED_HOSTS as the server hostname.
ALLOWED_HOSTS = [
    gethostname(),
    gethostbyname(gethostname()),
]

# load our specified PROFILE as our Environment for configs
ENVIORNMENT = os.environ['PROFILE']
print('Loading config file: '+BASE_DIR+'/resources/env-'+ENVIORNMENT+'.yml')
config = yaml.full_load(open(BASE_DIR+'/resources/env-'+ENVIORNMENT+'.yml'))

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'trad_plan_analysis',
    'bind_plan_analysis_api',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'control_panel.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'control_panel.wsgi.application'


# Database
# https://docs.djangoproject.com/en/2.2/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.environ['DB_NAME'] if "DB_NAME" in os.environ else config['DB']['NAME'],
        'USER': os.environ['DB_USER'] if "DB_USER" in os.environ else config['DB']['USER'],
        'PASSWORD': os.environ['DB_PASSWORD'] if "DB_PASSWORD" in os.environ else config['DB']['PASSWORD'],
        'HOST': os.environ['DB_HOST'] if "DB_HOST" in os.environ else config['DB']['HOST'],
        'PORT': os.environ['DB_PORT'] if "DB_PORT" in os.environ else config['DB']['PORT'],
    }
}

DATABASE_POOL_ARGS = {
    'max_overflow': 10,
    'pool_size': 5,
    'recycle': 300
}

# Password validation
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]
#     # 'rest_framework_simplejwt.authentication.JWTAuthentication',

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'jwtauthenticationextension.JWTTokenUserAuthenticationExt',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        #  'rest_framework.permissions.IsAuthenticated',
    )
}

# Internationalization
# https://docs.djangoproject.com/en/2.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.2/howto/static-files/

STATIC_URL = '/static/'


# Logging: make logs of level INFO or higher print to console
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
        },
        'django.db.backends': {
            'level': 'DEBUG',
            'handlers': ['console', ],
        },
        'control_panel': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
            'filters': []
        },
    },
}

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Project specfic constants
AUTHORIZATION_HEADER = 'System-Authorization'

# Project specific settings

PROCESS_COUNT = os.environ['PROCESS_COUNT'] if "PROCESS_COUNT" in os.environ else config['SETTINGS']['PROCESS_COUNT']
MOD = os.environ['MOD'] if "MOD" in os.environ else config['SETTINGS']['MOD']
BLOCK_QUEUE_SIZE = os.environ['BLOCK_QUEUE_SIZE'] if "BLOCK_QUEUE_SIZE" in os.environ else config['SETTINGS']['BLOCK_QUEUE_SIZE']

REFDB_HOST = os.environ['REFDB_HOST'] if "REFDB_HOST" in os.environ else config['REFDB']['HOST']
REFDB_DB = os.environ['REFDB_DB_NAME'] if "REFDB_DB_NAME" in os.environ else config['REFDB']['DB_NAME']
REFDB_USER = os.environ['REFDB_USERNAME'] if "REFDB_USERNAME" in os.environ else config['REFDB']['USERNAME']
REFDB_PASSWORD = os.environ['REFDB_PASSWORD'] if "REFDB_PASSWORD" in os.environ else config['REFDB']['PASSWORD']
REFDB_PORT = os.environ['REFDB_PORT'] if "REFDB_PORT" in os.environ else config['REFDB']['PORT']

KAFKA_URL = os.environ['KAFKA_HOST_URL'] if "KAFKA_HOST_URL" in os.environ else config['KAFKA']['HOST_URL']
KAFKA_QUOTING_REQUEST_TOPIC = os.environ['KAFKA_QUOTING_REQUEST_TOPIC'] if "KAFKA_QUOTING_REQUEST_TOPIC" in os.environ else config['KAFKA']['QUOTING_REQUEST_TOPIC']
KAFKA_QUOTING_RESULT_TOPIC = os.environ['KAFKA_QUOTING_RESULT_TOPIC'] if "KAFKA_QUOTING_RESULT_TOPIC" in os.environ else config['KAFKA']['QUOTING_RESULT_TOPIC']
KAFKA_ZOOKEEPER_URL = os.environ['KAFKA_ZOOKEEPER_URL'] if "KAFKA_ZOOKEEPER_URL" in os.environ else config['KAFKA']['ZOOKEEPER_URL']
KAFKA_CONSUMER_GROUP = os.environ['KAFKA_CONSUMER_GROUP'] if "KAFKA_CONSUMER_GROUP" in os.environ else config['KAFKA']['CONSUMER_GROUP']
KAFKA_SSL = os.environ['KAFKA_SSL'] if "KAFKA_SSL" in os.environ else config['KAFKA']['SSL'] if "SSL" in config['KAFKA'] else None

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False
