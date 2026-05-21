"""
Django settings for backend project.
Configured for:
  - PostgreSQL database
  - DRF Token Authentication
  - Gmail SMTP via .env
  - CORS for React frontend
"""

from pathlib import Path
import os
from dotenv import load_dotenv

# Load all variables from the root-level .env file
# The .env file lives two levels above this settings.py:
#   food-ordering-system/.env
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent.parent / '.env')

BASE_DIR = Path(__file__).resolve().parent.parent


# ─────────────────────────────────────────────
# Security
# ─────────────────────────────────────────────

SECRET_KEY = os.getenv('SECRET_KEY')

# Set to False in production and configure ALLOWED_HOSTS properly
DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1']


# ─────────────────────────────────────────────
# Installed Applications
# ─────────────────────────────────────────────

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party
    'corsheaders',
    'rest_framework',
    'rest_framework.authtoken',   # ← Required for Token Authentication

    # Project app
    'api',
]


# ─────────────────────────────────────────────
# Middleware
# ─────────────────────────────────────────────

MIDDLEWARE = [
    # CORS must be first
    'corsheaders.middleware.CorsMiddleware',

    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'backend.wsgi.application'


# ─────────────────────────────────────────────
# Database — PostgreSQL (no SQLite)
# ─────────────────────────────────────────────

DATABASES = {
    'default': {
        'ENGINE':   'django.db.backends.postgresql',
        'NAME':     os.getenv('DB_NAME'),
        'USER':     os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST':     os.getenv('DB_HOST', 'localhost'),
        'PORT':     os.getenv('DB_PORT', '5432'),
        'OPTIONS': {
            # Enforce UTC timestamps at the DB level
            'options': '-c timezone=UTC',
        },
    }
}


# ─────────────────────────────────────────────
# Django REST Framework
# ─────────────────────────────────────────────

REST_FRAMEWORK = {
    # Token auth is the primary method; session auth kept for admin/browsable API
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    # Default: endpoints are open unless explicitly restricted
    # (individual views use @login_required_json or IsAuthenticated)
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
    # Return clean JSON errors instead of HTML pages
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    # Throttle settings — basic brute-force protection
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '30/minute',   # unauthenticated requests
        'user': '60/minute',   # authenticated requests
    },
}


# ─────────────────────────────────────────────
# Password Validation
# ─────────────────────────────────────────────

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# ─────────────────────────────────────────────
# Internationalisation
# ─────────────────────────────────────────────

LANGUAGE_CODE = 'en-us'
TIME_ZONE     = 'UTC'
USE_I18N      = True
USE_TZ        = True   # ← MUST be True for timezone-aware OTP expiry checks


# ─────────────────────────────────────────────
# Static & Media Files
# ─────────────────────────────────────────────

STATIC_URL = 'static/'
MEDIA_URL  = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ─────────────────────────────────────────────
# CORS — Allow React dev server
# ─────────────────────────────────────────────

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
]

CORS_ALLOW_CREDENTIALS = True

# Expose the Authorization header so the frontend can read it
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]


# ─────────────────────────────────────────────
# Cache — used for OTP resend rate limiting
# ─────────────────────────────────────────────
# LocMemCache works per-process with no extra setup.
# Switch to Redis in production: django-redis + CACHE_BACKEND = 'django_redis.cache.RedisCache'
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}


# ─────────────────────────────────────────────
# Email — Gmail SMTP via App Password
# ─────────────────────────────────────────────
# Required .env variables:
#   EMAIL_HOST_USER     = your Gmail address
#   EMAIL_HOST_PASSWORD = 16-character Gmail App Password (not your login password)
#
# How to get a Gmail App Password:
#   1. Enable 2-Step Verification on your Google account
#   2. Go to: Google Account → Security → App Passwords
#   3. Generate a password for "Mail" / "Other"
#   4. Paste the 16-char code (without spaces) into .env

EMAIL_BACKEND       = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST          = 'smtp.gmail.com'
EMAIL_PORT          = 587
EMAIL_USE_TLS       = True
EMAIL_HOST_USER     = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL  = EMAIL_HOST_USER


# ─────────────────────────────────────────────
# Logging — surface OTP events in the console
# ─────────────────────────────────────────────

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{levelname}] {asctime} {module}: {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class':     'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'api': {
            'handlers':  ['console'],
            'level':     'INFO',
            'propagate': False,
        },
    },
}
