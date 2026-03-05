from .base import *

DEBUG = False


ALLOWED_HOSTS = [
    h.strip() for h in os.getenv("ALLOWED_HOSTS", "").split(",") if h.strip()
]

INSTALLED_APPS += ["storages"]


FRONTEND_URLS = os.getenv("FRONTEND_URLS", "")
CORS_ALLOWED_ORIGINS = [
    url.strip() for url in FRONTEND_URLS.split(",") if url.strip()
]
# Security
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
X_FRAME_OPTIONS = "DENY"
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# AWS S3
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_STORAGE_BUCKET_NAME = os.getenv("AWS_STORAGE_BUCKET_NAME")
AWS_S3_REGION_NAME = os.getenv("AWS_S3_REGION_NAME")

AWS_S3_CUSTOM_DOMAIN = f"{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com"

AWS_QUERYSTRING_AUTH = True
AWS_QUERYSTRING_EXPIRE = 3600 
AWS_S3_SIGNATURE_VERSION = "s3v4" 
AWS_DEFAULT_ACL = None
AWS_S3_FILE_OVERWRITE = False
AWS_S3_OBJECT_PARAMETERS = {
    "CacheControl": "max-age=86400",
}

AWS_LOCATION_STATIC = "static"
AWS_LOCATION_MEDIA = "media"

# Static
STATIC_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/static/"

# Media
MEDIA_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/media/"


STORAGES = {
    "default": {
        "BACKEND": "config.storages.MediaStorage",
    },
    "staticfiles": {
        "BACKEND": "config.storages.StaticStorage",
    },
}

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": os.getenv("REDIS_URL", "redis://127.0.0.1:6379/1"),
        "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
    }
}

REST_FRAMEWORK.update({
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.UserRateThrottle",
        "rest_framework.throttling.AnonRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "user": "20/min",
        "anon": "5/min",
    }
})