from . import Engine

class DumbEngine(Engine):
    """
        a dumb proof-of-concept engine that creates a delivery attempt to the first available
        contact
    """

    def create_attempts(self, unscheduled_mrs):
        for mr in unscheduled_mrs:
            first_contact = mr.recipient.contacts.all()[0]
            self.create_attempt(first_contact, mr)

