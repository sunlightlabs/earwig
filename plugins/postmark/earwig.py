'''
Incoming mail and bounce requests are each handled with a webhook.
http://developer.postmarkapp.com/developer-inbound-configure.html
'''
import re

import pystmark

from django.conf import settings
from django.template import Context
from django.template.loader import get_template

from contact.models import DeliveryStatus
from ..base.plugin import BasePlugin
from .models import PostmarkDeliveryMeta


class PostmarkPlugin(BasePlugin):
    '''Send an email from through the postmark API.
    '''
    medium = 'email'

    def get_reply_to(self, message_recip):
        if settings.POSTMARK_MX_FORWARDING_ENABLED:
            inbound_host = settings.EARWIG_INBOUND_EMAIL_HOST
        else:
            inbound_host = settings.POSTMARK_INBOUND_HOST
        reply_to_tmpl = '{0.POSTMARK_INBOUND_HASH}+{1.id}@{2}'
        reply_to = reply_to_tmpl.format(settings, message_recip, inbound_host)
        return reply_to

    def send(self, to, reply_to, subject, body_txt, body_html):
        '''Send an email using stock earwig sender, reply-to addresses.
        '''
        message = pystmark.Message(
            sender=settings.EARWIG_EMAIL_SENDER,
            reply_to=reply_to,
            to=to,
            subject=subject,
            text=body_txt,
            html=body_html)
        api_key = getattr(settings, 'POSTMARK_API_KEY', None)
        response = pystmark.send(message, api_key)
        resp_json = response.json()
        return resp_json

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

        message = attempt.messages.get()
        reply_to = self.get_reply_to(message)

        resp_json = self.send(
            recipient_email_address, reply_to, subject, body_txt, body_html)

        message_id = resp_json.get('MessageID')
        if message_id is None:
            attempt.mark_attempted(
                status=DeliveryStatus.invalid,
                plugin='postmark',
                template='default')
            return

        meta = PostmarkDeliveryMeta.objects.create(
            attempt=attempt, message_id=message_id)

        # Mark the attempt sent.
        attempt.mark_attempted(
            status=DeliveryStatus.sent,
            plugin='postmark',
            template='default')
        if debug:
            return {
                "text": body_txt,
                "html": body_html,
                "subject": subject,
                "obj": meta
            }

    def send_reply_notification(self, message_reply, debug=False):
        reply_to = self.get_reply_to(message_reply.message_recip)
        to = message_reply.recipient_email()

        # Is this wrongish?
        if to is None:
            return

        ctx = dict(
            message_reply=message_reply,
            login_url=getattr(settings, 'LOGIN_URL', 'PUT REAL LOGIN URL HERE'))

        # Render the email components.
        path = 'plugins/default/email/forwarded_reply/body.html'
        body_html = self.render_template(path, **ctx)
        path = 'plugins/default/email/forwarded_reply/body.txt'
        body_txt = self.render_template(path, **ctx)
        path = 'plugins/default/email/forwarded_reply/subject.txt'
        subject = self.render_template(path, **ctx)

        self.send(to, reply_to, subject, body_txt, body_html)

    def render_template(self, path, **kwargs):
        template = get_template(path)
        result = template.render(Context(kwargs))
        return re.sub(r'\n{3,}', '\n\n', result).strip()
