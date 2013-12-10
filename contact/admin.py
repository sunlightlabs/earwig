from django.contrib import admin
from contact.models import (
    Person,
    ContactDetail,
    Sender,
    DeliveryAttempt,
    Message,
    MessageRecipient,
)


admin.site.register(Person)
admin.site.register(ContactDetail)
admin.site.register(Sender)
admin.site.register(DeliveryAttempt)
admin.site.register(Message)
admin.site.register(MessageRecipient)
