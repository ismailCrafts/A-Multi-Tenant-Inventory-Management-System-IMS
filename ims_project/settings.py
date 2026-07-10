# ==========================================================
# DJANGO SETTINGS (Step-by-step with env variables)
# ==========================================================
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env file
load_dotenv(os.path.join(BASE_DIR, ".env"))


# -------------------------------
# Step 1: Base directory
# -------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent


# -------------------------------
# Step 2: Security settings
# -------------------------------
# SECRET_KEY should always be set via environment variable in production
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "unsafe-default-key")

# DEBUG mode (default True for dev, set False in production)
DEBUG = os.environ.get("DJANGO_DEBUG", "True").lower() in ["true", "1", "yes"]



# Allowed hosts (comma-separated string in env)
ALLOWED_HOSTS = [h.strip() for h in os.environ.get("DJANGO_ALLOWED_HOSTS", "").split(",") if h.strip()]



# -------------------------------
# Step 3: Custom user model
# -------------------------------
AUTH_USER_MODEL = 'authenticate_app.User'


# -------------------------------
# Step 4: Installed apps
# -------------------------------
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Project apps
    'authenticate_app.apps.AuthenticateAppConfig',
    'dashboard_app.apps.DashboardAppConfig',
    'product_app.apps.ProductAppConfig',
    'stock_app.apps.StockAppConfig',
    'personinfo_app.apps.PersoninfoAppConfig',
    'report_app.apps.ReportAppConfig',
]


# -------------------------------
# Step 5: Middleware
# -------------------------------
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


# -------------------------------
# Step 6: URL and WSGI
# -------------------------------
ROOT_URLCONF = 'ims_project.urls'
WSGI_APPLICATION = 'ims_project.wsgi.application'
LOGIN_URL = '/login/'



# -------------------------------
# Step 7: Templates
# -------------------------------
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')], 
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.i18n',
            ],
        },
    },
]


# -------------------------------
# Step 8: Database (PostgreSQL)
# -------------------------------
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get("POSTGRES_DB", "ims_db"),
        'USER': os.environ.get("POSTGRES_USER", "ims_user"),
        'PASSWORD': os.environ.get("POSTGRES_PASSWORD", "ismailbhuyan12"),
        'HOST': os.environ.get("POSTGRES_HOST", "localhost"),
        'PORT': os.environ.get("POSTGRES_PORT", "5432"),
    }
}


# -------------------------------
# Step 9: Email settings
# -------------------------------
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.environ.get("EMAIL_HOST", "localhost")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", 587))
EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "False") == "True"
EMAIL_USE_SSL = os.environ.get("EMAIL_USE_SSL", "False") == "True"
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER


# -------------------------------
# Step : errors capture
# -------------------------------

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'django_errors.log'),
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'django.request': {
            'handlers': ['file', 'console'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
}







# -------------------------------
# Step 10: Password validation
# -------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# -------------------------------
# Step 11: Internationalization
# -------------------------------
LANGUAGE_CODE = 'en-us'   # default
USE_I18N = True
USE_L10N = True
USE_TZ = True

LANGUAGES = [
    ('en', 'English'),
    ('bn', 'বাংলা'),
]

LOCALE_PATHS = [
    os.path.join(BASE_DIR, 'locale'), # translations will live here
]


AUTHENTICATION_BACKENDS = [
    'authenticate_app.backends.TenantUsernameBackend',  # ← tries username+org first
    'django.contrib.auth.backends.ModelBackend',        # ← fallback for superusers/admin
]



# -------------------------------
# Step 12: Static & Media files
# -------------------------------
STATIC_URL = '/static/'   # must start and end with a slash

# Where collectstatic will gather all static files for production
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Extra static directories (for dev only)
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]

# Media (user uploads)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# use in local server when debug = false and store static
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"




# -------------------------------
# Step 13: Default primary key type
# -------------------------------
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


if not DEBUG:
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
