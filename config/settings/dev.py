from .base import *
from dotenv import load_dotenv
load_dotenv()

DEBUG = True
ALLOWED_HOSTS = ['127.0.0.1','localhost']
CORS_ALLOW_ALL_ORIGINS = True


STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
