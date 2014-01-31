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
    def __init__(self, sender, to, subject, text):
        self.sender = sender
        self.to = to
        self.subject = subject
        self.text = text


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
