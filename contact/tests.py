import json
import datetime
from django.test import TestCase, Client
from django.utils.timezone import utc
from .models import Person, Sender, Message, MessageRecipient
from .views import _msg_to_json

GOOD_MESSAGE = {'type': 'public', 'subject': 'hi', 'message': 'this is a message',
                'sender': '1'*64, 'recipients': ['ocd-person/1']}
EXPIRY = datetime.datetime(2020, 1, 1, tzinfo=utc)
ISOFORMAT = '%Y-%m-%dT%H:%M:%S.%f+00:00'


class TestCreateSender(TestCase):

    def test_basic_sender(self):
        """ ensure that the sender is created """
        c = Client()
        resp = c.post('/sender/', {'email': 'test@example.com', 'name': 'Test', 'ttl': 7})
        data = json.loads(resp.content)
        assert data['email'] == 'test@example.com'
        assert data['name'] == 'Test'
        # ensure it was created in the last minute
        created_at = datetime.datetime.strptime(data['created_at'], ISOFORMAT)
        assert created_at - datetime.datetime.utcnow() < datetime.timedelta(minutes=1)
        # ensure it expires ~7 days from now
        expires_at = datetime.datetime.strptime(data['email_expires_at'], ISOFORMAT)
        assert (datetime.timedelta(days=6, hours=23) < expires_at - datetime.datetime.utcnow() <
                datetime.timedelta(days=7))
        # object should exist in db now
        assert Sender.objects.count() == 1

    def test_updated_sender(self):
        """ ensure that the sender updates if a field changes """
        # post the initial sender
        c = Client()
        resp = c.post('/sender/', {'email': 'test@example.com', 'name': 'Test', 'ttl': 7})
        assert Sender.objects.get().name == 'Test'
        assert Sender.objects.count() == 1

        # post the update
        resp = c.post('/sender/', {'email': 'test@example.com', 'name': 'Updated', 'ttl': 7})
        assert Sender.objects.get().name == 'Updated'
        assert Sender.objects.count() == 1

    def test_updated_ttl(self):
        """ ensure that ttl gets extended if longer """
        c = Client()
        resp = c.post('/sender/', {'email': 'test@example.com', 'name': 'Test', 'ttl': 7})
        resp = c.post('/sender/', {'email': 'test@example.com', 'name': 'Test', 'ttl': 70})
        # new expiry time should be at least 69 days in the future
        assert (Sender.objects.get().email_expires_at -
                datetime.datetime.utcnow().replace(tzinfo=utc) >
                datetime.timedelta(days=69, hours=23))

    def test_non_updated_ttl(self):
        """ ensure that ttl doesn't get shortened """
        c = Client()
        resp = c.post('/sender/', {'email': 'test@example.com', 'name': 'Test', 'ttl': 7})
        resp = c.post('/sender/', {'email': 'test@example.com', 'name': 'Test', 'ttl': 1})
        # new expiry time should be at least 6 days in the future
        assert (Sender.objects.get().email_expires_at -
                datetime.datetime.utcnow().replace(tzinfo=utc) >
                datetime.timedelta(days=6, hours=23))

    def test_revived_sender(self):
        """ ensure that an expired sender can be revived with an email and good ttl """
        c = Client()
        resp = c.post('/sender/', {'email': 'test@example.com', 'name': 'Test', 'ttl': 7})
        Sender.objects.update(email_expires_at=datetime.datetime.utcnow().replace(tzinfo=utc),
                              email=None)
        resp = c.post('/sender/', {'email': 'test@example.com', 'name': 'Test', 'ttl': 7})
        assert Sender.objects.count() == 1
        assert Sender.objects.get().email == 'test@example.com'
        # new expiry time should be at least 6 days in the future
        assert (Sender.objects.get().email_expires_at -
                datetime.datetime.utcnow().replace(tzinfo=utc) >
                datetime.timedelta(days=6, hours=23))


class TestCreateMessage(TestCase):

    def setUp(self):
        self.person1 = Person.objects.create(ocd_id='ocd-person/1', title='President',
                                             name='Gerald Fnord')
        self.person2 = Person.objects.create(ocd_id='ocd-person/2', title='Mayor',
                                             name='Rob Fnord')
        self.sender = Sender.objects.create(id='1'*64, email="test@example.com",
                                            email_expires_at=EXPIRY)

    def test_msg_to_json(self):
        """ test that msg to json works """
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

    def test_sender_payload_good(self):
        """ ensure that a sender payload is created and used properly """
        c = Client()
        Sender.objects.all().delete()
        msg = GOOD_MESSAGE.copy()
        msg['sender'] = '{"email": "phil@example.com", "name": "Phil", "ttl": 7}'
        resp1 = c.post('/message/', msg)
        msg['sender'] = '{"email": "phil@example.com", "name": "Phillip", "ttl": 7}'
        resp2 = c.post('/message/', msg)
        assert resp1.status_code == 200
        assert resp2.status_code == 200
        # creates one and only one
        assert Sender.objects.count() == 1

    def test_sender_payload_bad(self):
        """ 400 returned when payload isn't complete or invalid JSON """
        c = Client()
        msg = GOOD_MESSAGE.copy()

        # incomplete
        msg['sender'] = '{"junk": "stuff"}'
        resp = c.post('/message/', msg)
        assert resp.status_code == 400
        assert 'missing field' in resp.content

        # non-JSON
        msg['sender'] = '~not even json~'
        resp = c.post('/message/', msg)
        assert resp.status_code == 400
        assert 'invalid JSON' in resp.content

    def test_bad_sender(self):
        """ ensure that bad senders are flagged """
        c = Client()
        msg = GOOD_MESSAGE.copy()
        msg['sender'] = '9'*64      # bad id
        response = c.post('/message/', msg)
        assert response.status_code == 400
        assert 'sender' in response.content

    def test_bad_recipient(self):
        """ invalid recipients should raise an error """
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
        """ multiple recipients should work """
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
        self.sender = Sender.objects.create(id='1'*64, email_expires_at=EXPIRY)
        msg = Message.objects.create(type='private', sender=self.sender, subject='subject',
                                     message='hello everyone')
        MessageRecipient.objects.create(message=msg, recipient=self.person1, status='pending')
        MessageRecipient.objects.create(message=msg, recipient=self.person2, status='expired')

    def test_get_message(self):
        """ basic get message """
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
        """ make-believe message """
        c = Client()
        resp = c.get('/message/33/')
        assert resp.status_code == 404
