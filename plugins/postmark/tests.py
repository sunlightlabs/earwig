import json

from django.test import TestCase
from django.test import Client
from django.core.urlresolvers import reverse

from contact.models import DeliveryAttempt
from plugins.postmark.models import PostmarkDeliveryMeta


class BounceFeedbackTest(TestCase):
    '''Verify that a hypothetical bounce notifaction from postmark results
    in an accurate RecieverFeedback record.
    '''
    fixtures = ['contact_attempt.json']

    def test_hard_bounce(self):
        '''Verify that hard bounces result in DeliveryAttempt.status
        being toggled to 'invalid'.
        '''
        attempt = DeliveryAttempt.objects.get(pk=1)

        # Assume an email message has been sent.
        PostmarkDeliveryMeta.objects.create(attempt=attempt, message_id='test-hard-bounce')

        # Simulate a bounce notification from postmark.
        client = Client()
        payload = {
            "ID": [],
            "Type": "HardBounce",
            "Tag": "Invitation",
            "MessageID": "test-hard-bounce",
            "TypeCode": 1,
            "Email": "jim@test.com",
            "BouncedAt": "2010-04-01",
            "Details": "test bounce",
            "DumpAvailable": True,
            "Inactive": True,
            "CanActivate": True,
            "Subject": "Hello from our app!"
        }
        client.post(reverse('handle_bounce'), json.dumps(payload),
                    content_type='application/json')

        attempt = DeliveryAttempt.objects.get(pk=1)

        # Make sure the hard bounce was recorded as vendor-hard-bounce.
        self.assertEqual(attempt.status, 'invalid')

    def test_blocked(self):
        '''Verify that "blocked" notifcations from postmark result in
        a RecieverFeedback instance with feedback_type = 'vendor-blocked'.
        '''
        attempt = DeliveryAttempt.objects.all()[0]

        # Assume an email message has been sent.
        PostmarkDeliveryMeta.objects.create(attempt=attempt, message_id='test-blocked')

        # Simulate a bounce notification from postmark.
        client = Client()
        payload = {
            "ID": [],
            "Type": "Blocked",
            "Tag": "Invitation",
            "MessageID": "test-blocked",
            "TypeCode": 1,
            "Email": "jim@test.com",
            "BouncedAt": "2010-04-01",
            "Details": "test bounce",
            "DumpAvailable": True,
            "Inactive": True,
            "CanActivate": True,
            "Subject": "Hello from our app!"
        }
        client.post(reverse('handle_bounce'), json.dumps(payload), content_type='application/json')

        feedback = attempt.feedback.get()

        # Make sure the hard bounce was recorded as vendor-hard-bounce.
        self.assertEqual(feedback.feedback_type, 'contact-detail-blacklist')
