import os
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

TIME_ZONE = 'America/New_York'
LANGUAGE_CODE = 'en-us'
USE_I18N = False
USE_L10N = True
USE_TZ = True

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'kombu.transport.django',
    'contact',
    'plugins.fnord',
    'plugins.twilio_sms',
    'plugins.twilio_voice',
    'plugins.postmark',
    'plugins.ses',
    'engine',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'earwig.urls'
WSGI_APPLICATION = 'earwig.wsgi.application'

STATIC_URL = "/static/"

TEMPLATE_DIRS = (
    os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'templates')),
)

ALLOWED_HOSTS = []
