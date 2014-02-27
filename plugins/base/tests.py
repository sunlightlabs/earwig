import datetime
from django.utils.timezone import utc
from django.db import IntegrityError
from contact.models import (Person, ContactDetail, Sender, DeliveryAttempt, Message,
                            MessageRecipient, Application)


class BaseTests(object):

    def make_delivery_attempt(self, type, value, blacklisted=False):
        cd = ContactDetail.objects.create(person=self.person, type=type, value=value,
                                          blacklisted=blacklisted)
        attempt = DeliveryAttempt.objects.create(contact=cd, status='scheduled',
                                                 template='default', engine='default')
        attempt.messages.add(self.mr)
        return attempt

    def setUp(self):
        super(BaseTests, self).setUp()
        app = Application.objects.create(name="test", contact="fnord@fnord.fnord",
                                         template_set="None", active=True)
        send = Sender.objects.create(id='randomstring',
                                     email_expires_at=datetime.datetime(2020, 1, 1, tzinfo=utc))

        self.person = Person.objects.create(ocd_id='test', title='Mr.', name='Paul Tagliamonte',
                                            photo_url="")

        message = Message.objects.create(type='fnord', sender=send, subject="Hello, World",
                                         message="HELLO WORLD", application=app)
        self.mr = MessageRecipient.objects.create(message=message, recipient=self.person,
                                                  status='pending')

        self.email_attempt = self.make_delivery_attempt(type='email', value='test@example.com')
        self.good_attempt = self.make_delivery_attempt(type=self.plugin.medium,
                                                       value='555-222-2222')
        self.bad_type_attempt = self.make_delivery_attempt(type='junk', value='555')

    def test_duplicate(self):
        """
        Verify the plugin raises an error if it gets two identical messages to send.
        """
        self.plugin.send_message(self.good_attempt, debug=True)

        with self.assertRaises(IntegrityError):
            self.plugin.send_message(self.good_attempt, debug=True)

    def test_blacklist(self):
        '''
        Verify the plugin raises an error if it the contact detail is blacklisted.
        '''
        blacklist_attempt = self.make_delivery_attempt(type=self.plugin.medium,
                                                       value='555-222-1111',
                                                       blacklisted=True)
        with self.assertRaises(ValueError):
            self.plugin.send_message(blacklist_attempt, debug=True)

    def test_wrong_medium(self):
        '''
        Verify that the plugin balks if told to send wrong type.
        '''
        # TODO: try multiple bad types based on current plugin
        with self.assertRaises(ValueError):
            self.plugin.send_message(self.bad_type_attempt, debug=True)
