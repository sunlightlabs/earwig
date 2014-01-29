from .base import *     # noqa

DEBUG = True
TEMPLATE_DEBUG = DEBUG

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'earwig.sqlite3'),
    }
}

CONTACT_PLUGIN_TWILIO = {
    "account_sid": "",
    "auth_token": "",
    "from_number": "",
}

SECRET_KEY = '36bit6i^@#wq7is-^0nm7&)hh)1o0_szde_4&5fu_9zkh70_v&'
EARWIG_SENDER_SALT = 'the-very-saltiest'
EARWIG_PUBLIC_LINK_ROOT = "http://localhost:8000"
