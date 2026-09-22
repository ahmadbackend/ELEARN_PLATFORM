"""
Django settings for ELEARN_BACKEND.

The project is API-only: it serves /api/v1/, the OpenAPI docs, the admin and the
peer-chat websocket. The user interface is the SPA in ELEARN_FRONTEND/.

Everything environment specific is read from the environment so the same image
runs locally, in docker compose and anywhere else. See .env.example.
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def env(name, default=None):
    return os.environ.get(name, default)


def env_bool(name, default=False):
    return str(env(name, str(default))).strip().lower() in ('1', 'true', 'yes', 'on')


def env_list(name, default=''):
    return [item.strip() for item in env(name, default).split(',') if item.strip()]


# ----------------------------------------------------------------------------- core
SECRET_KEY = os.environ['DJANGO_SECRET_KEY']
DEBUG = env_bool('DJANGO_DEBUG', False)
ALLOWED_HOSTS = env_list('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1')
# behind nginx/compose the browser's origin is not the one Django sees
CSRF_TRUSTED_ORIGINS = env_list('DJANGO_CSRF_TRUSTED_ORIGINS')

INSTALLED_APPS = [
    'daphne',
    'channels',
    'django_celery_results',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'HOME_AREA',
    'STUDENT',
    'INSTRUCTOR',
    'rest_framework',
    'drf_spectacular',
    'django_celery_beat',
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

ROOT_URLCONF = 'ELEARN_BACKEND.urls'
WSGI_APPLICATION = 'ELEARN_BACKEND.wsgi.application'
ASGI_APPLICATION = 'ELEARN_BACKEND.asgi.application'

# only the admin, the DRF browsable API and the swagger UI render templates now
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

# ----------------------------------------------------------------------------- database
if env('DJANGO_DB_ENGINE', 'sqlite') == 'postgres':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': env('POSTGRES_DB', 'elearn'),
            'USER': env('POSTGRES_USER', 'elearn'),
            'PASSWORD': env('POSTGRES_PASSWORD', ''),
            'HOST': env('POSTGRES_HOST', 'db'),
            'PORT': env('POSTGRES_PORT', '5432'),
            'CONN_MAX_AGE': int(env('POSTGRES_CONN_MAX_AGE', '60')),
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# STUDENT and INSTRUCTOR are separate tables with their own backends; ModelBackend stays
# for django.contrib.auth's own superusers (the admin site)
AUTHENTICATION_BACKENDS = [
    'HOME_AREA.AuthCust.StudentBackend',
    'HOME_AREA.AuthCust.InstructorBackend',
    'django.contrib.auth.backends.ModelBackend',
]

# ----------------------------------------------------------------------------- redis
# one server, one logical database per concern: 0 celery, 1 cache, 2 channels
REDIS_URL = env('REDIS_URL', 'redis://127.0.0.1:6379')


def redis_db(number, override):
    return env(override) or '{}/{}'.format(REDIS_URL.rstrip('/'), number)


CELERY_BROKER_URL = redis_db(0, 'CELERY_BROKER_URL')
CELERY_RESULT_BACKEND = 'django-db'
CELERY_TIMEZONE = env('CELERY_TIMEZONE', 'UTC')
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': redis_db(1, 'CACHE_URL'),
        'OPTIONS': {'CLIENT_CLASS': 'django_redis.client.DefaultClient'},
    }
}

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {'hosts': [redis_db(2, 'CHANNELS_URL')]},
    }
}

# ----------------------------------------------------------------------------- rest api
# the SPA sends a JWT as `Authorization: Bearer <token>` (see HOME_AREA/authentication.py)
# and never uses cookies; session auth is only there so an admin can browse the API
REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'HOME_AREA.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.IsAuthenticated'],
    'DEFAULT_PAGINATION_CLASS': 'HOME_AREA.pagination.StandardPagination',
    'PAGE_SIZE': 12,
    'DEFAULT_RENDERER_CLASSES': (
        ['rest_framework.renderers.JSONRenderer', 'rest_framework.renderers.BrowsableAPIRenderer']
        if DEBUG else ['rest_framework.renderers.JSONRenderer']
    ),
    # activation and reset codes are six digits, so the unauthenticated auth endpoints
    # are rate limited per IP to keep them out of brute-force range
    'DEFAULT_THROTTLE_CLASSES': ['rest_framework.throttling.ScopedRateThrottle'],
    'DEFAULT_THROTTLE_RATES': {
        'login': env('THROTTLE_LOGIN', '10/min'),
        'register': env('THROTTLE_REGISTER', '5/hour'),
        'code': env('THROTTLE_CODE', '8/min'),
    },
}

# seconds an api token stays valid (7 days)
API_TOKEN_MAX_AGE = int(env('API_TOKEN_MAX_AGE', 60 * 60 * 24 * 7))

SPECTACULAR_SETTINGS = {
    'TITLE': 'ELEARN platform API',
    'DESCRIPTION': 'REST API behind the ELEARN single-page app. Log in at /api/v1/auth/login/ '
                   'and send the token as `Authorization: Bearer <token>`.',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
    'SCHEMA_PATH_PREFIX': '/api/v1',
}

# CORS is only needed when the SPA is served from another origin. Behind the bundled
# nginx the SPA and the API share one origin and this list stays empty.
# django-cors-headers is optional: without it the API still works same-origin.
CORS_ALLOWED_ORIGINS = env_list('CORS_ALLOWED_ORIGINS')
# the SPA authenticates with a header, never a cookie, so credentialed CORS is not needed
CORS_ALLOW_CREDENTIALS = False

try:
    import corsheaders  # noqa: F401

    INSTALLED_APPS.append('corsheaders')
    # must sit above CommonMiddleware so preflight requests are answered first
    MIDDLEWARE.insert(0, 'corsheaders.middleware.CorsMiddleware')
except ImportError:
    pass

# ----------------------------------------------------------------------------- i18n / files
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# explicit leading slash: nginx serves both prefixes off the shared volumes
STATIC_URL = '/static/'
STATIC_ROOT = Path(env('DJANGO_STATIC_ROOT', BASE_DIR / 'staticfiles'))
MEDIA_URL = '/media/'
MEDIA_ROOT = Path(env('DJANGO_MEDIA_ROOT', BASE_DIR / 'media'))

DATA_UPLOAD_MAX_MEMORY_SIZE = int(env('DATA_UPLOAD_MAX_MEMORY_SIZE', 25 * 1024 * 1024))
FILE_UPLOAD_MAX_MEMORY_SIZE = DATA_UPLOAD_MAX_MEMORY_SIZE

# ----------------------------------------------------------------------------- email
EMAIL_HOST = env('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_HOST_USER = env('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', '')
EMAIL_PORT = int(env('EMAIL_PORT', 587))
EMAIL_USE_TLS = env_bool('EMAIL_USE_TLS', True)
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', EMAIL_HOST_USER or 'no-reply@example.com')
# without smtp credentials, print the activation codes to the log instead of failing
if not EMAIL_HOST_USER:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# ----------------------------------------------------------------------------- hardening
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'
X_FRAME_OPTIONS = 'DENY'
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = 'same-origin'

if not DEBUG:
    # set DJANGO_SECURE_SSL=True once the deployment terminates TLS
    SECURE_SSL_REDIRECT = env_bool('DJANGO_SECURE_SSL', False)
    SESSION_COOKIE_SECURE = SECURE_SSL_REDIRECT
    CSRF_COOKIE_SECURE = SECURE_SSL_REDIRECT
    SECURE_HSTS_SECONDS = int(env('DJANGO_HSTS_SECONDS', 0))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = bool(SECURE_HSTS_SECONDS)
    SECURE_HSTS_PRELOAD = bool(SECURE_HSTS_SECONDS)
    # nginx terminates TLS and passes the scheme on
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {'simple': {'format': '{levelname} {asctime} {name} {message}', 'style': '{'}},
    'handlers': {'console': {'class': 'logging.StreamHandler', 'formatter': 'simple'}},
    'root': {'handlers': ['console'], 'level': env('DJANGO_LOG_LEVEL', 'INFO')},
}
