from django.test import TestCase, Client
from .models import Person, Sender, Message

GOOD_MESSAGE = {'type': 'public', 'subject': 'hi', 'message': 'this is a message',
                'sender': '1-2-3-4', 'recipients': ['ocd-person/1']}

class TestCreateMessage(TestCase):

    def setUp(self):
        Person.objects.create(ocd_id='ocd-person/1', title='Mayor', name='Ford')
        Sender.objects.create(uid='1-2-3-4')

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
