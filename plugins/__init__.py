from contact.errors import CantCancelMessage, Blacklisted


class ContactPlugin(object):
    """ """
    def check_contact_detail(self, attempt):
        '''Code might send messages by calling this method.
        '''
        contact_detail = attempt.contact

        # Verify the contact detail is not blacklisted.
        if contact_detail.blacklisted:
            msg = '%s is blacklisted.'
            raise Blacklisted(msg % contact_detail.value)

        # Verify the correct contact detail type has been passed.
        if contact_detail.type != self.medium:
            msg = "'%s' only supports messages of type %r"
            raise InvalidContactType(msg % (self.__class__, self.medium))

    def send_message(self, attempt):
        """ """
        raise NotImplementedError()

    def check_message_status(self, attempt):
        """ """
        raise NotImplementedError()

    def cancel_message(self, attempt):
        """ """
        raise CantCancelMessage("Can't cancel the message")
