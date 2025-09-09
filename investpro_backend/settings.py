"""
Django settings for investpro_backend project.
"""

from pathlib import Path
from datetime import timedelta
import os
import environ

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent

# Setup environ
env = environ.Env(
    DJANGO_DEBUG=(bool, False)
)

# Auto-pick correct .env file
ENV_FILE = BASE_DIR / ".env.production" if os.getenv("DJANGO_ENV") == "production" else BASE_DIR / ".env.development"
environ.Env.read_env(ENV_FILE)

# Debug & Secret
DEBUG = env("DJANGO_DEBUG")
SECRET_KEY = env("DJANGO_SECRET_KEY")

print("🔧 Loaded environment file:", ENV_FILE)
print("🔧 DJANGO_ENV:", os.getenv("DJANGO_ENV"))
print("🔧 DEBUG =", DEBUG)


print("DEBUG ENV:", os.getenv("DJANGO_ENV"))
print("Using env file:", ENV_FILE)
print("Loaded DJANGO_SECRET_KEY:", env("DJANGO_SECRET_KEY", default="NOT FOUND"))

# Hosts
ALLOWED_HOSTS = [
    "heritageinvestmentgrup.com",
    "www.heritageinvestmentgrup.com",
    "localhost",
    "127.0.0.1",
]

# Security (production only)
if not DEBUG:
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

# Apps
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "core",
    "anymail",
    "rest_framework",
    "corsheaders",
]

# Middleware
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",  # must come early
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# CSRF & CORS
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://heritageinvestmentgrup.com",
    "https://www.heritageinvestmentgrup.com",
]

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "https://heritageinvestmentgrup.com",
]

# DRF + SimpleJWT
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
}

# Templates
ROOT_URLCONF = "investpro_backend.urls"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "investpro_backend.wsgi.application"

# Database (SQLite for dev, replace with Postgres in prod)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Static & Media
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Primary key field
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Email / Anymail (Brevo)
EMAIL_BACKEND = "anymail.backends.brevo.EmailBackend"

ANYMAIL = {
    "BREVO_API_KEY": env("BREVO_API_KEY"),
    "BREVO_SEND_DEFAULTS": {
        "from_email": env("DEFAULT_FROM_EMAIL"),
    },
}
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL")

# Admins
ADMINS = [
    ("Site Owner", env("DEFAULT_FROM_EMAIL")),
]
