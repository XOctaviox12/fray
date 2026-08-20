import socket
import time
import logging
import environ
from pathlib import Path
import os
import cloudinary

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent

# ── Carga de variables de entorno (única fuente de verdad) ───────────────────
env = environ.Env()
environ.Env.read_env(os.path.join(BASE_DIR, '.env'), overwrite=True)

# ── Seguridad básica ─────────────────────────────────────────────────────────
SECRET_KEY = env('SECRET_KEY')
DEBUG = env.bool('DEBUG', default=False)
ALLOWED_HOSTS = [h.strip() for h in env('ALLOWED_HOSTS', default='localhost').split(',') if h.strip()]

APPEND_SLASH = True

# ── Aplicaciones ─────────────────────────────────────────────────────────────
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'cloudinary_storage',
    'django.contrib.staticfiles',
    'cloudinary',
    'corsheaders',
    'academic',
    'inicio',
    'users',
    'campuses',
    'docente',
    'tutor',
]

# ── Cloudinary y Storages (Adaptativo Local / Producción) ─────────────────────
CLOUDINARY_STORAGE = {
    'CLOUD_NAME': env('CLOUDINARY_CLOUD_NAME'),
    'API_KEY':    env('CLOUDINARY_API_KEY'),
    'API_SECRET': env('CLOUDINARY_API_SECRET'),
    'RESOURCE_TYPE': 'raw',
    'SECURE': True,
}

# Configuración inteligente: Estáticos locales si DEBUG=True, Cloudinary si es producción
STORAGES = {
    "default": {
        "BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

# Variable de compatibilidad para evitar bloqueos en librerías externas
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

# ── Middleware ────────────────────────────────────────────────────────────────
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

# ── Templates ─────────────────────────────────────────────────────────────────
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'academic' / 'templates'],
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

WSGI_APPLICATION = 'core.wsgi.application'

# ── Base de datos (Happy Eyeballs IPv4/IPv6) ──────────────────────────────────
def _pick_reachable_ip(hostname, port, timeout=2, attempts=2, prefer_ipv4_first=True):
    if not hostname:
        return hostname

    try:
        candidates = socket.getaddrinfo(
            hostname, int(port), proto=socket.IPPROTO_TCP
        )
    except socket.gaierror as e:
        logger.warning("No se pudo resolver %s: %s. Se usará el hostname tal cual.", hostname, e)
        return hostname

    def sort_key(c):
        is_ipv4 = c[0] == socket.AF_INET
        if prefer_ipv4_first:
            return 0 if is_ipv4 else 1
        return 0 if not is_ipv4 else 1

    seen = set()
    unique_candidates = []
    for c in candidates:
        key = (c[0], c[4][0])
        if key not in seen:
            seen.add(key)
            unique_candidates.append(c)
    unique_candidates.sort(key=sort_key)

    for family, socktype, proto, canonname, sockaddr in unique_candidates:
        ip = sockaddr[0]
        family_name = "IPv4" if family == socket.AF_INET else "IPv6"
        for attempt in range(1, attempts + 1):
            try:
                with socket.socket(family, socket.SOCK_STREAM) as s:
                    s.settimeout(timeout)
                    s.connect((ip, int(port)))
                logger.info("Conexión DB verificada vía %s (%s), intento %d.", ip, family_name, attempt)
                return ip
            except OSError as e:
                logger.warning(
                    "Fallo probando %s (%s) intento %d/%d: %s",
                    ip, family_name, attempt, attempts, e,
                )
                if attempt < attempts:
                    time.sleep(0.3)

    logger.warning(
        "Ninguna IP de %s respondió tras probar todas las opciones; "
        "se usará el hostname original y se deja que el sistema decida.",
        hostname,
    )
    return hostname

DB_HOST_RAW = env('DB_HOST', default=None)
DB_PORT_RAW = env('DB_PORT', default='5432')
DB_HOST_RESOLVED = _pick_reachable_ip(DB_HOST_RAW, DB_PORT_RAW)

DATABASES = {
    'default': {
        'ENGINE':   env('DB_ENGINE', default='django.db.backends.postgresql'),
        'NAME':     env('DB_NAME', default=None),
        'USER':     env('DB_USER', default=None),
        'PASSWORD': env('DB_PASSWORD', default=None),
        'HOST':     DB_HOST_RESOLVED,
        'PORT':     DB_PORT_RAW,
        'CONN_MAX_AGE': 60,
        'OPTIONS': {
            'sslmode': 'require',
            'connect_timeout': 10,
            'keepalives': 1,
            'keepalives_idle': 30,
            'keepalives_interval': 10,
            'keepalives_count': 3,
        },
    }
}

# ── Validación de contraseñas ─────────────────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ── Internacionalización ──────────────────────────────────────────────────────
LANGUAGE_CODE = 'es-mx'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# ── Archivos estáticos y media ────────────────────────────────────────────────
STATIC_URL  = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL   = '/media/'
MEDIA_ROOT  = BASE_DIR / 'media'

STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ── CORS ──────────────────────────────────────────────────────────────────────
CORS_ALLOW_ALL_ORIGINS = False
_cors_env = env('CORS_ALLOWED_ORIGINS', default=None)
CORS_ALLOWED_ORIGINS = (
    [o.strip() for o in _cors_env.split(',') if o.strip()]
    if _cors_env else
    ["http://localhost:8100", "http://localhost:4200"]
)

# ── Auth ──────────────────────────────────────────────────────────────────────
AUTH_USER_MODEL       = 'users.User'
LOGIN_URL             = 'login'
LOGIN_REDIRECT_URL    = 'dashboard'
LOGOUT_REDIRECT_URL   = 'login'

# ── Seguridad de producción ──────────────────────────────────────────────────
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = env.bool('SECURE_SSL_REDIRECT', default=True)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_REFERRER_POLICY = 'same-origin'
    X_FRAME_OPTIONS = 'DENY'

    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

    _csrf_trusted = env('CSRF_TRUSTED_ORIGINS', default=None)
    if _csrf_trusted:
        CSRF_TRUSTED_ORIGINS = [o.strip() for o in _csrf_trusted.split(',') if o.strip()]

# ── Logging ──────────────────────────────────────────────────────────────────
PASSWORD_RECOVERY_KEY = env('PASSWORD_RECOVERY_KEY', default=None)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{asctime}] {levelname} {name}: {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': env('DJANGO_LOG_LEVEL', default='INFO'),
            'propagate': False,
        },
    },
}