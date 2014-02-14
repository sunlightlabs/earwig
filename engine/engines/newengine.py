from .base import Engine

# Queue of 15 messages to 3 people over the last 3 hours.
#
# Output a 15 DAs to 3 people. Default to email unless it doesn't exist,
# in which case, use the Voice. If that's not there. leave pending. (emit
# warning?)
#
# Try with 1 of each (email, number, none). Expect 10 DAs, and 5 pending
# messages


def get_prefered_contact_detail(contacts, methods):
    if methods is None:
        raise ValueError("No methods given")

    try:
        type_ = next(methods)
    except StopIteration:
        raise ValueError("No matching contact type")

    for contact in contacts:
        if contact.type == type_:
            return contact

    return get_prefered_contact_detail(contacts, methods=methods)



class NewEngine(Engine):
    def create_attempts(self, unscheduled_mrs):
        for mr in unscheduled_mrs:
            contacts = mr.recipient.contacts.all()

            try:
                detail = get_prefered_contact_detail(
                    contacts,
                    iter(["email", "voice", "sms"])
                )
            except ValueError:
                print("SOME_ERROR_CONDITION")
                return

            self.create_attempt(detail, mr)
