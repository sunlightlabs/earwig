from __future__ import print_function


import importlib
import datetime
import uuid
import pytz
from django.core.management.base import BaseCommand, CommandError
from contact.models import (
    Person,
    ContactDetail,
    Sender,
    DeliveryAttempt,
    Message,
    Application,
    MessageRecipient,
)


def create_test_attempt(value, type_):
    pt = Person.objects.create(ocd_id='ocd-person/%s' % (uuid.uuid4()),
                               title='Mr.',
                               name='John Q. Public',
                               photo_url="")

    cd = ContactDetail.objects.create(person=pt, type=type_, value=value, note='Manual test',
                                      blacklisted=False)

    send = Sender.objects.create(
        id=uuid.uuid4(),
        email="example@example.com",
        email_expires_at=datetime.datetime.now(pytz.timezone('US/Eastern')),
    )

    app = Application.objects.create(name="test", contact="fnord@fnord.fnord",
                                     template_set="None", active=True)
    app.save()

    message = Message(type=type_, sender=send, subject="Hello, World",
                      message="HELLO WORLD", application=app)
    message.save()

    mr = MessageRecipient(message=message, recipient=pt, status='pending')
    mr.save()

    attempt = DeliveryAttempt(contact=cd, status="scheduled",
                              template='default',
                              created_at=datetime.datetime.now(pytz.timezone('US/Eastern')),
                              updated_at=datetime.datetime.now(pytz.timezone('US/Eastern')),
                              engine="default")
    attempt.save()
    attempt.messages.add(mr)
    return attempt


class Command(BaseCommand):
    args = '<plugin_id msg_type contact_value>'
    help = 'Send a test message'

    def handle(self, plugin_id, type_, value, *args, **options):
        module_name = "plugins.%s.earwig" % (plugin_id)

        mod = importlib.import_module(module_name)
        name = "%sContact" % (plugin_id.title().replace("_", ""))

        try:
            plugin = getattr(mod, name)
        except AttributeError:
            raise CommandError('No such plugin `%s` in module `%s`' % (
                name,
                module_name
            ))

        attempt = create_test_attempt(value, type_)
        plugin = plugin()
        print("Sending:")
        print("")
        print(plugin.send_message(attempt))
        print("")

        #attempt.delete()
