import os
from pathlib import Path
import environ
from datetime import timedelta
from corsheaders.defaults import default_headers, default_methods

BASE_DIR = Path(__file__).resolve().parent.parent

# ----------------------
# Environment variables
# ----------------------
env = environ.Env(DEBUG=(bool, False))

DJANGO_ENV = os.getenv("DJANGO_ENV", "production")
DEBUG = DJANGO_ENV == "development"

env_file = BASE_DIR / f".env.{DJANGO_ENV}"

if env_file.exists():
    environ.Env.read_env(env_file)
else:
    print(f"⚠️ {env_file} not found, relying on system environment variables.")

# ----------------------
# Security
# ----------------------
SECRET_KEY = env("DJANGO_SECRET_KEY", default="unsafe-secret-key")


DEBUG = DJANGO_ENV == "development"

ALLOWED_HOSTS = [
    "octa-investment.com",
    "api.octa-investment.com",
    ".railway.app",
    "localhost",
    "127.0.0.1",
]




# ----------------------
# Applications
# ----------------------
INSTALLED_APPS = [
    "jazzmin",
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

# ----------------------
# Middleware
# ----------------------
# settings.py
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # MUST be here
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]




# STATICFILES_STORAGE = "whitenoise.storage.CompressedStaticFilesStorage"
# settings.py


# ----------------------
# CORS / CSRF
# ----------------------
from corsheaders.defaults import default_headers, default_methods

if DJANGO_ENV == "development":
    # Local React dev
    CORS_ALLOWED_ORIGINS = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
    CSRF_TRUSTED_ORIGINS = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
    CORS_ALLOW_ALL_ORIGINS = True   # ✅ useful for dev
    CSRF_COOKIE_SECURE = False
    SESSION_COOKIE_SECURE = False

else:
    CORS_ALLOWED_ORIGINS = [
        "https://octa-investment.com",
        "https://www.octa-investment.com",
        "https://api.octa-investment.com",
    ]


CSRF_TRUSTED_ORIGINS = [
    "https://octa-investment.com",
    "https://api.octa-investment.com",
]



CORS_ALLOW_CREDENTIALS = True




CORS_ALLOW_HEADERS = list(default_headers) + [
    "authorization",
    "content-type",
]
CORS_ALLOW_METHODS = list(default_methods)
# 🔥 TURN THIS OFF ON RAILWAY
SECURE_SSL_REDIRECT = False

USE_X_FORWARDED_HOST = True

# ----------------------
# SSL / Proxy
# ----------------------
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# ----------------------
# Django REST Framework & JWT
# ----------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "UNAUTHENTICATED_USER": None,
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# ----------------------
# URLs / Templates
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


STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# ==========================
# DJANGO ADMIN LOGIN FIX
# ==========================

SESSION_ENGINE = "django.contrib.sessions.backends.db"

SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"

SESSION_COOKIE_DOMAIN = None
CSRF_COOKIE_DOMAIN = None

LOGIN_REDIRECT_URL = "/admin/"
LOGOUT_REDIRECT_URL = "/admin/login/"




FRONTEND_URL = env("FRONTEND_URL", default="http://localhost:3000")

# ----------------------
# Default primary key
# ----------------------
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ====================
# Brevo Email Settings
# ====================
# BREVO_API_KEY = os.getenv("BREVO_API_KEY", "")



# Default sender (must be verified in Brevo dashboard)
# DEFAULT_FROM_EMAIL = "no-reply@heritageinvestmentgrup.com"
# DEFAULT_FROM_NAME = "Heritage Investment"
