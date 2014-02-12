from .engines import Engine
# Queue of 15 messages to 3 people over the last 3 hours.
# 
# Output a 15 DAs to 3 people. Default to email unless it doesn't exist,
# in which case, use the Voice. If that's not there. leave pending. (emit
# warning?)
# 
# Try with 1 of each (email, number, none). Expect 10 DAs, and 5 pending
# messages


class NewEngine(Engine):
    def create_attempts(self, unscheduled_mrs):
        for mr in unscheduled_mrs:
            contacts = mr.recipient.contacts.all()

            detail = None
            for contact in contacts:
                if contact.type == 'email':
                    detail = contact
                    break
            else:
                for contact in contacts:
                    if contact.type == 'voice':
                        detail = contact
                        break

            if detail is None:
                print("SOME_ERROR_CONDITION_HERE")

            self.create_attempt(detail, mr)
