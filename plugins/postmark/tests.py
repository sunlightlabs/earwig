import json

from django.test import TestCase
from django.test import Client
from django.core.urlresolvers import reverse

from contact.models import DeliveryAttempt, ReceiverFeedback
from plugins.postmark.models import PostmarkDeliveryMeta


class BounceFeedbackTest(TestCase):
    '''Verify that a hypothetical bounce notifaction from postmark results
    in an accurate RecieverFeedback record.
    '''
    fixtures = ['contact_attempt.json',]

    def test_hard_bounce(self):
        attempt = DeliveryAttempt.objects.all()[0]

        # Assume an email message has been sent.
        meta = PostmarkDeliveryMeta.objects.create(
            attempt=attempt, message_id='test-email')

        # Simulate a bounce notification from postmark.
        client = Client()
        payload = {
            "ID" : [],
            "Type" : "HardBounce",
            "Tag" : "Invitation",
            "MessageID" : "test-email",
            "TypeCode" : 1,
            "Email" : "jim@test.com",
            "BouncedAt" : "2010-04-01",
            "Details" : "test bounce",
            "DumpAvailable" : True,
            "Inactive" : True,
            "CanActivate" : True,
            "Subject" : "Hello from our app!"
            }
        client.post(reverse('handle_bounce'), json.dumps(payload),
                    content_type='application/json')

        feedback = attempt.feedback.get()

        # Make sure the hard bounce was recorded as vendor-hard-bounce.
        self.assertEqual(feedback.feedback_type, 'vendor-hard-bounce')


