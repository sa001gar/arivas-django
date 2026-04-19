# Key fixes:
# - Disable SSL redirect on local runserver
# - Keep Cloudflare responsible for SSL/HSTS
# - Fix static handling compatibility
# - Ensure safe DEBUG=False local execution

import os
import sys
from pathlib import Path
from urllib.parse import urlparse
from django.core.exceptions import ImproperlyConfigured
from django.templatetags.static import static
from django.utils.functional import lazy
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# --- ENV HELPERS ---
def env_bool(name, default=False):
    return os.getenv(name, str(default)).lower() in ("true", "1", "yes", "on")


def env_str(name, default=None, required=False):
    val = os.getenv(name)
    if not val:
        if required:
            raise ImproperlyConfigured(f"Missing env: {name}")
        return default
    return val.strip()


def env_list(name, default=None):
    val = os.getenv(name)
    if not val:
        return default or []
    return [v.strip() for v in val.split(",") if v.strip()]


# --- CORE ---
DEBUG = env_bool("DEBUG", True)
USE_R2 = env_bool("USE_R2", False)
R2_PUBLIC_MEDIA_URL = env_str("R2_PUBLIC_MEDIA_URL", "")

SECRET_KEY = env_str("SECRET_KEY", "dev-key", required=not DEBUG)

# --- HOSTS ---
def normalize_host(h):
    if not h:
        return ""
    if "://" in h:
        h = urlparse(h).netloc
    return h.split(":")[0]

ALLOWED_HOSTS = [normalize_host(h) for h in env_list("ALLOWED_HOSTS", ["127.0.0.1", "localhost"]) if h]

if not DEBUG and not ALLOWED_HOSTS:
    raise ImproperlyConfigured("ALLOWED_HOSTS required in production")


# --- APPS ---
INSTALLED_APPS = [
    "unfold",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "app",
    "django_summernote",
    "tailwind",
    "theme",
    "fontawesomefree",
    "whitenoise.runserver_nostatic",
]

if USE_R2 and "storages" not in INSTALLED_APPS:
    INSTALLED_APPS.append("storages")


# --- MIDDLEWARE ---
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


# --- STATIC ---
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

RUNNING_RUNSERVER = len(sys.argv) > 1 and sys.argv[1] == "runserver"

USE_MANIFEST = not DEBUG

if RUNNING_RUNSERVER and not (STATIC_ROOT / "staticfiles.json").exists():
    USE_MANIFEST = False

STATICFILES_STORAGE = (
    "django.contrib.staticfiles.storage.StaticFilesStorage"
    if not USE_MANIFEST
    else "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"
)

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": STATICFILES_STORAGE,
    },
}

if USE_R2:
    r2_account_id = env_str("R2_ACCOUNT_ID", "")
    r2_access_key_id = env_str("R2_ACCESS_KEY_ID", "")
    r2_secret_access_key = env_str("R2_SECRET_ACCESS_KEY", "")
    r2_bucket_name = env_str("R2_BUCKET_NAME", "")
    r2_endpoint_url = env_str("R2_ENDPOINT_URL", "")

    missing = []
    if not r2_access_key_id:
        missing.append("R2_ACCESS_KEY_ID")
    if not r2_secret_access_key:
        missing.append("R2_SECRET_ACCESS_KEY")
    if not r2_bucket_name:
        missing.append("R2_BUCKET_NAME")
    if not R2_PUBLIC_MEDIA_URL:
        missing.append("R2_PUBLIC_MEDIA_URL")
    if not (r2_endpoint_url or r2_account_id):
        missing.append("R2_ENDPOINT_URL or R2_ACCOUNT_ID")

    if missing:
        raise ImproperlyConfigured(
            "R2 storage is enabled but required settings are missing: " + ", ".join(missing)
        )

    aws_s3_endpoint_url = r2_endpoint_url or f"https://{r2_account_id}.r2.cloudflarestorage.com"

    STORAGES["default"] = {
        "BACKEND": "arivas.storage_backends.PublicMediaURLS3Storage",
        "OPTIONS": {
            "access_key": r2_access_key_id,
            "secret_key": r2_secret_access_key,
            "bucket_name": r2_bucket_name,
            "region_name": os.getenv("R2_REGION", "auto"),
            "endpoint_url": aws_s3_endpoint_url,
            "default_acl": None,
            "querystring_auth": False,
            "file_overwrite": False,
            "object_parameters": {
                "CacheControl": os.getenv("R2_CACHE_CONTROL", "public, max-age=86400"),
            },
        },
    }

WHITENOISE_AUTOREFRESH = DEBUG
WHITENOISE_USE_FINDERS = DEBUG
WHITENOISE_MANIFEST_STRICT = True


# --- MEDIA ---
MEDIA_URL = R2_PUBLIC_MEDIA_URL.rstrip("/") + "/" if USE_R2 and R2_PUBLIC_MEDIA_URL else "/media/"
MEDIA_ROOT = BASE_DIR / "media"


# --- DATABASE ---
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


# --- URLS / WSGI ---
ROOT_URLCONF = "arivas.urls"
WSGI_APPLICATION = "arivas.wsgi.application"

# --- TEMPLATES ---
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
    }
]


# --- SUMMERNOTE ---
lazy_static = lazy(static, str)

SUMMERNOTE_CONFIG = {
    "css": (
        lazy_static("css/dist/styles.css"),
    ),
}


# --- UNFOLD ---
UNFOLD = {
    "SITE_ICON": {
        "light": lambda req: static("assets/images/logo.avif"),
        "dark": lambda req: static("assets/images/logo.avif"),
    },
}


DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
