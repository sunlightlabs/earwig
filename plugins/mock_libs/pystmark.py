import uuid
import datetime


class Message(object):
    '''
    message = pystmark.Message(
    sender='twneale@gmail.com',
    to=recipient_email_address,
    subject=subject,
    text=body)
    '''
    def __init__(self, sender, reply_to, to, subject, text, html):
        self.sender = sender
        self.reply_to = reply_to
        self.to = to
        self.subject = subject
        self.text = text
        self.html = html

    def __eq__(self, other):
        if self.sender != other.sender:
            return False
        if self.reply_to != other.reply_to:
            return False
        if self.to != other.to:
            return False
        if self.subject != other.subject:
            return False
        if self.text != other.text:
            return False
        if self.html != other.html:
            return False
        return True


class Response(object):

    def __init__(self, message):
        self.message = message

    def json(self):
        return {
            'ErrorCode': 0,
            'To': self.message.sender,
            'Message': 'OK',
            'SubmittedAt': datetime.datetime.utcnow().isoformat(),
            'MessageID': uuid.uuid4()}


def send(message, *args):
    return Response(message)


BOUNCED_EMAIL_ID = 'BOUNCED_EMAIL'


def get_bounces(api_key):
    class Response(object):
        '''I feel so unclean.'''
        def json(self):
            return {
                'TotalCount': 1,
                'Bounces': [{
                    "ID": 'cow',
                    "Type": "HardBounce",
                    "MessageID": BOUNCED_EMAIL_ID,
                    "TypeCode": 1,
                    "Details": "test bounce",
                    "Email": "jim@test.com",
                    "BouncedAt": "[YESTERDAY]",
                    "DumpAvailable": True,
                    "Inactive": True,
                    "CanActivate": True,
                    "Content": "Return-Path:....",
                    "Subject": "Hello from our app!"
                }]
            }
    return Response()
