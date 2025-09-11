# investpro_backend/settings.py
import os
from pathlib import Path
import environ
from datetime import timedelta

# ----------------------
# Paths
# ----------------------
BASE_DIR = Path(__file__).resolve().parent.parent

# ----------------------
# Environment variables
# ----------------------
env = environ.Env(
    DEBUG=(bool, False)
)


DJANGO_ENV = os.environ.get("DJANGO_ENV", "development")
env_file = BASE_DIR / f".env.{DJANGO_ENV}"

if env_file.exists():
    environ.Env.read_env(env_file)
else:
    print(f"⚠️ {env_file} not found, relying on system environment variables.")

# ----------------------
# Security
# ----------------------

SECRET_KEY = env("DJANGO_SECRET_KEY", default="fallback-secret-key")

DEBUG = env.bool("DJANGO_DEBUG", default=(DJANGO_ENV == "development"))
ALLOWED_HOSTS = env.list(
    "DJANGO_ALLOWED_HOSTS",
    default=["127.0.0.1", "localhost", "heritageinvestmentgrup.com", "www.heritageinvestmentgrup.com"]
)

# ----------------------
# Applications
# ----------------------

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "corsheaders",
    "core",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",  # Must be first
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# CSRF + CORS
CSRF_TRUSTED_ORIGINS = [
    "https://web-production-eb3c87.up.railway.app",
    "https://heritageinvestmentgrup.com",
    "https://www.heritageinvestmentgrup.com",
]
CORS_ALLOWED_ORIGINS = [
    "https://heritageinvestmentgrup.com",
    "https://www.heritageinvestmentgrup.com",
]
CORS_ALLOW_CREDENTIALS = True

# SSL settings (for Railway behind proxy)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True

# ----------------------
# Django REST Framework
# ----------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    )
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# ----------------------
# URLs and Templates
# ----------------------
ROOT_URLCONF = "investpro_backend.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
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

# ----------------------
# Database
# ----------------------
DATABASES = {
    "default": env.db(
        "DATABASE_URL",
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}"
    )
}

# ----------------------
# Password validation
# ----------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ----------------------
# Internationalization
# ----------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# ----------------------
# Static files
# ----------------------
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"] if (BASE_DIR / "static").exists() else []

# ----------------------
# Default primary key
# ----------------------
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
