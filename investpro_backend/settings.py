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
DJANGO_ENV = os.environ.get("DJANGO_ENV", "development")
env_file = BASE_DIR / f".env.{DJANGO_ENV}"

if env_file.exists():
    environ.Env.read_env(env_file)
else:
    print(f"⚠️ {env_file} not found, relying on system environment variables.")

# ----------------------
# Security
# ----------------------
SECRET_KEY = os.getenv("SECRET_KEY", "unsafe-secret-key")
DEBUG = os.getenv("DEBUG", "False") == "True"

ALLOWED_HOSTS = env.list(
    "DJANGO_ALLOWED_HOSTS",
    default=[
        "127.0.0.1",
        "localhost",
        "octa-invest.onrender.com",
        "octa-investment.com",
        "www.octa-investment.com",
    ],
)

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
    "corsheaders.middleware.CorsMiddleware",  # must be very first
    "django.middleware.security.SecurityMiddleware",
    'whitenoise.middleware.WhiteNoiseMiddleware',
    "django.middleware.common.CommonMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    
]

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

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
    # Production domains
    CORS_ALLOWED_ORIGINS = [
        "https://octa-investment.com",
        "https://www.octa-investment.com",
        "https://octa-invest.onrender.com",
    ]

    CSRF_TRUSTED_ORIGINS = [
        "https://octa-investment.com",
        "https://www.octa-investment.com",
    ]

    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True


# Common settings
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = list(default_headers) + [
    "authorization",
    "content-type",
]
CORS_ALLOW_METHODS = list(default_methods)


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
    )
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
STATICFILES_DIRS = [BASE_DIR / "static"] if (BASE_DIR / "static").exists() else []


FRONTEND_URL = env("FRONTEND_URL", default="http://localhost:3000")

# ----------------------
# Default primary key
# ----------------------
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ====================
# Brevo Email Settings
# ====================
BREVO_API_KEY = env("BREVO_API_KEY")  

# Default sender (must be verified in Brevo dashboard)
DEFAULT_FROM_EMAIL = "no-reply@heritageinvestmentgrup.com"
DEFAULT_FROM_NAME = "Heritage Investment"
