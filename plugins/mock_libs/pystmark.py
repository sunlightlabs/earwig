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
    def __init__(self, sender, to, subject, text, html):
        self.sender = sender
        self.to = to
        self.subject = subject
        self.text = text
        self.html = html


class Response(object):

    def __init__(self, message):
        self.message = message

    def json(self):
        return {
            u'ErrorCode': 0,
            u'To': self.message.sender,
            u'Message': u'OK',
            u'SubmittedAt': datetime.datetime.utcnow().isoformat(),
            u'MessageID': uuid.uuid4()}


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
