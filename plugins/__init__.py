from contact.errors import Blacklisted


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
            raise ValueError(msg % (self.__class__, self.medium))

    def send_message(self, attempt):
        """ """
        raise NotImplementedError()

    def check_message_status(self, attempt):
        """ """
        raise NotImplementedError()


class EmailContactPlugin(ContactPlugin):
    '''
    '''
    def get_body_template(self, attempt):
        raise NotImplementedError()

    def get_subject_template(self, attempt):
        raise NotImplementedError()

    def get_sender_address(self, attempt):
        raise NotImplementedError()

    def get_reply_addreses(self, attempt):
        raise NotImplementedError()


class EmailDeliveryStatus(object):
    '''This is dumb, will evolve when we understand more about
    how each email API behaves.
    '''
    def __init__(self, status, data):
        self.status = status
        self.data = data
