'''
Incoming mail and bounce requests are each handled with a webhook.
http://developer.postmarkapp.com/developer-inbound-configure.html
'''
import re

import pystmark

from django.conf import settings
from django.template import Context
from django.template.loader import get_template

from ..base.plugin import BasePlugin
from ..utils import body_template_to_string, subject_template_to_string
from .models import PostmarkDeliveryMeta


class PostmarkContact(BasePlugin):
    '''Send an email from through the postmark API.
    '''
    medium = 'email'

    def send_message(self, attempt, debug=False):
        contact_detail = attempt.contact
        self.check_contact_detail(contact_detail)
        recipient_email_address = contact_detail.value

        ctx = dict(
            attempt=attempt,
            login_url=getattr(settings, 'LOGIN_URL', 'PUT REAL LOGIN URL HERE'))

        path = 'plugins/default/email/body.html'
        body_html = self.render_template(path, **ctx)

        path = 'plugins/default/email/body.txt'
        body_txt = self.render_template(path, **ctx)

        path = 'plugins/default/email/subject.txt'
        subject = self.render_template(path, **ctx)

        message = pystmark.Message(
            sender=settings.EARWIG_EMAIL_SENDER,
            to=recipient_email_address,
            subject=subject,
            text=body_txt,
            html=body_html)

        api_key = getattr(settings, 'POSTMARK_API_KEY', None)
        response = pystmark.send(message, api_key)
        resp_json = response.json()
        message_id = resp_json['MessageID']
        meta = PostmarkDeliveryMeta.objects.create(
            attempt=attempt, message_id=message_id)

        if debug:
            return {
                "text": body_txt,
                "html": body_html,
                "subject": subject,
                "obj": meta
            }

    def render_template(self, path, **kwargs):
        template = get_template(path)
        result = template.render(Context(kwargs))
        return re.sub(r'\n{3,}', '\n\n', result).strip()
