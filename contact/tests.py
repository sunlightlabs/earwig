import json
import datetime
from django.test import TestCase, Client
from .models import Person, Sender, Message, MessageRecipient
from .views import _msg_to_json

GOOD_MESSAGE = {'type': 'public', 'subject': 'hi', 'message': 'this is a message',
                'sender': '1-2-3-4', 'recipients': ['ocd-person/1']}

class TestCreateMessage(TestCase):

    def setUp(self):
        self.person1 = Person.objects.create(ocd_id='ocd-person/1', title='President',
                                             name='Gerald Fnord')
        self.person2 = Person.objects.create(ocd_id='ocd-person/2', title='Mayor',
                                             name='Rob Fnord')
        self.sender = Sender.objects.create(id='1-2-3-4', email_expires_at=datetime.datetime.now())

    def test_get_message(self):
        msg = Message.objects.create(type='private', sender=self.sender, subject='subject',
                                     message='hello everyone')
        MessageRecipient.objects.create(message=msg, recipient=self.person1, status='pending')
        MessageRecipient.objects.create(message=msg, recipient=self.person2, status='expired')

        data = json.loads(_msg_to_json(msg))

        assert data['message'] == 'hello everyone'
        assert data['type'] == 'private'
        assert data['sender'] == self.sender.id
        assert data['subject'] == 'subject'
        assert len(data['recipients']) == 2
        assert data['recipients'][0]['status'] == 'pending'
        assert data['recipients'][0]['recipient_id'] == self.person1.id
        assert data['recipients'][1]['status'] == 'expired'
        assert data['recipients'][1]['recipient_id'] == self.person2.id

    def test_required_fields(self):
        """ test that type, subject, message, sender are required """
        c = Client()

        for field in ('type', 'subject', 'message', 'sender'):
            msg = GOOD_MESSAGE.copy()
            # remove field
            msg.pop(field)
            # post to endpoint
            response = c.post('/message/', msg)

            # assert failure
            assert response.status_code == 400
            # ensure fieldname is mentioned in response
            assert field in response.content

    def test_bad_sender(self):
        """ ensure that bad senders are flagged """
        c = Client()
        msg = GOOD_MESSAGE.copy()
        msg['sender'] = 'not-even-a-uuid'
        response = c.post('/message/', msg)
        assert response.status_code == 400
        assert 'sender' in response.content

    def test_bad_recipient(self):
        c = Client()
        msg = GOOD_MESSAGE.copy()
        msg['recipients'] = ['ocd-person/NaN']
        response = c.post('/message/', msg)
        assert response.status_code == 400
        assert 'recipient' in response.content

    def test_ok_message(self):
        """ ensure that good messages return OK & create a Message object """
        c = Client()
        response = c.post('/message/', GOOD_MESSAGE.copy())
        assert response.status_code == 200
        assert Message.objects.count() == 1
        assert MessageRecipient.objects.count() == 1

        # reconstitute message out of response
        data = json.loads(response.content)
        assert data['type'] == GOOD_MESSAGE['type']
        assert data['subject'] == GOOD_MESSAGE['subject']
        assert data['message'] == GOOD_MESSAGE['message']

    def test_multi_recipient(self):
        c = Client()
        msg = GOOD_MESSAGE.copy()
        msg['recipients'] = ['ocd-person/1', 'ocd-person/2']
        response = c.post('/message/', msg)
        assert response.status_code == 200
        assert Message.objects.count() == 1
        assert MessageRecipient.objects.count() == 2


class TestGetMessage(TestCase):

    def setUp(self):
        self.person1 = Person.objects.create(ocd_id='ocd-person/1', title='President',
                                             name='Gerald Fnord')
        self.person2 = Person.objects.create(ocd_id='ocd-person/2', title='Mayor',
                                             name='Rob Fnord')
        self.sender = Sender.objects.create(id='1-2-3-4', email_expires_at=datetime.datetime.now())
        msg = Message.objects.create(type='private', sender=self.sender, subject='subject',
                                     message='hello everyone')
        MessageRecipient.objects.create(message=msg, recipient=self.person1, status='pending')
        MessageRecipient.objects.create(message=msg, recipient=self.person2, status='expired')

    def test_get_message(self):
        c = Client()
        resp = c.get('/message/1/')
        data = json.loads(resp.content)

        assert data['message'] == 'hello everyone'
        assert data['type'] == 'private'
        assert data['sender'] == self.sender.id
        assert data['subject'] == 'subject'
        assert len(data['recipients']) == 2
        assert data['recipients'][0]['status'] == 'pending'
        assert data['recipients'][0]['recipient_id'] == self.person1.id
        assert data['recipients'][1]['status'] == 'expired'
        assert data['recipients'][1]['recipient_id'] == self.person2.id

    def test_get_message_404(self):
        c = Client()
        resp = c.get('/message/33/')
        assert resp.status_code == 404
