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
    # To get the following:
    #
    # Create a new account and log in.
    #
    # On the homepage (https://www.twilio.com/user/account), there are two
    # bits of text 'twixt the top menu / upgrade hero and the 'API Explorer'
    # and 'App Monitor' that says 'ACCOUNT SID' and 'AUTH TOKEN'. You have to
    # click the lock icon to show the 'AUTH TOKEN'.
    #
    # Fill that out below.
    "account_sid": "",
    "auth_token": "",
    # To get your number click 'NUMBERS' on the top nav bar. There'll be
    # a listing of numbers. Pick whichever one makes sense and paste it below.
    # The format doesn't seem to matter all that much, just copy-paste it from
    # whatever view you want.
    "from_number": "",
}

SECRET_KEY = '36bit6i^@#wq7is-^0nm7&)hh)1o0_szde_4&5fu_9zkh70_v&'
EARWIG_SENDER_SALT = 'the-very-saltiest'
EARWIG_PUBLIC_LINK_ROOT = "http://localhost:8000"
EARWIG_EMAIL_SENDER = 'tneale@sunlightfoundation.com'

# -----------------------------------------------------------------------------
# Postmark settings.
# https://postmarkapp.com/sign_up?reload=true
POSTMARK_API_KEY = 'cow'
POSTMARK_INBOUND_HASH = 'moo'
POSTMARK_INBOUND_HOST = 'inbound.postmarkapp.com'

# True if we set yourearwig.com as the domain of the reply-to
# messager rather than inbound.postmarkapp.com. Used in deciding
# whether the reply-to domain is ours or theirs.
POSTMARK_MX_FORWARDING_ENABLED = False

# If running own email host.
EARWIG_INBOUND_EMAIL_HOST = None
