# ============================================================
# CONFIGURACIÓN PRINCIPAL DEL BACKEND (DJANGO + API REST)
# ============================================================
# Este archivo configura toda la aplicación Django
# Aquí se definen: base de datos, autenticación, CORS, JWT, etc.

import os
from pathlib import Path
from datetime import timedelta
from dotenv import load_dotenv
import dj_database_url

# Carga variables de entorno desde archivo .env
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# Configuración básica de seguridad
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "django-insecure-replace-me")
DEBUG = os.getenv("DJANGO_DEBUG", "True") == "True"
ALLOWED_HOSTS = os.getenv("DJANGO_ALLOWED_HOSTS", "*").split(",")

# Apps instaladas - extensiones y funcionalidades
# rest_framework: para crear APIs REST
# rest_framework_simplejwt: para autenticación con JWT (tokens)
# corsheaders: permite que el frontend (Vue.js) se comunique con el backend
# store: nuestra app principal con modelos de usuarios, instrumentos, órdenes, etc.
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt",
    "corsheaders",
    "store",
]

# Middleware - procesa las peticiones HTTP
# corsheaders: permite peticiones desde otros orígenes (frontend)
# AuthenticationMiddleware: identifica al usuario autenticado
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "enfa_backend.urls"

# Configuración de plantillas HTML (no se usa aquí, es para APIs)
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

WSGI_APPLICATION = "enfa_backend.wsgi.application"

# ============================================================
# BASE DE DATOS - POSTGRESQL
# ============================================================
# Conecta con PostgreSQL para guardar:
# - Usuarios y autenticación
# - Instrumentos musicales y sus imágenes
# - Órdenes de compra
# - Listas de deseos
# - Reseñas y valoraciones
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL:
    DATABASES = {
        "default": dj_database_url.parse(DATABASE_URL, conn_max_age=600)
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.getenv("POSTGRES_DB", "enfa_db"),
            "USER": os.getenv("POSTGRES_USER", "enfa_user"),
            "PASSWORD": os.getenv("POSTGRES_PASSWORD", "enfa_pass"),
            "HOST": os.getenv("POSTGRES_HOST", "localhost"),
            "PORT": os.getenv("POSTGRES_PORT", "5432"),
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_L10N = True
USE_TZ = True

STATIC_URL = "/static/"
MEDIA_URL = "/media/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_ROOT = BASE_DIR / "media"

# Use WhiteNoise static files storage in production
STATICFILES_STORAGE = os.getenv(
    "STATICFILES_STORAGE",
    "whitenoise.storage.CompressedManifestStaticFilesStorage",
)

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
# Usamos modelo de usuario personalizado en store.User
AUTH_USER_MODEL = "store.User"

# ============================================================
# CORS - Permite que el frontend en Vue.js se comunique
# ============================================================
# CORS_ALLOW_ALL_ORIGINS: permite peticiones desde cualquier origen
# (en producción, restringir a dominios específicos)
# CORS_ALLOW_CREDENTIALS: permite enviar cookies/tokens
# Configure CORS origins via env var (comma-separated). If not set, allow all only in DEBUG.
DJANGO_CORS_ALLOWED = os.getenv("DJANGO_CORS_ALLOWED_ORIGINS")
if DJANGO_CORS_ALLOWED:
    CORS_ALLOWED_ORIGINS = DJANGO_CORS_ALLOWED.split(",")
    CORS_ALLOW_ALL_ORIGINS = False
else:
    CORS_ALLOW_ALL_ORIGINS = DEBUG

CORS_ALLOW_CREDENTIALS = True

# ============================================================
# API REST - Configuración de Django REST Framework
# ============================================================
# JWTAuthentication: cada petición debe incluir un token JWT en Authorization header
# IsAuthenticated: todas las vistas requieren estar autenticado por defecto
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
}

# ============================================================
# JWT - Tokens de autenticación
# ============================================================
# ACCESS_TOKEN: válido por 60 minutos (acceso a la app)
# REFRESH_TOKEN: válido por 7 días (se usa para obtener nuevo access token)
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=int(os.getenv("JWT_ACCESS_LIFETIME_MINUTES", "60"))),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=int(os.getenv("JWT_REFRESH_LIFETIME_DAYS", "7"))),
}

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "True") == "True"
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "no-reply@enfa.com")
