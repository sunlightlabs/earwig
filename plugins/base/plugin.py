
class BasePlugin(object):
    """ """
    def check_contact_detail(self, contact_detail):
        '''Code might send messages by calling this method.
        '''
        # Verify the contact detail is not blacklisted.
        if contact_detail.blacklisted:
            msg = '%s is blacklisted.'
            raise ValueError(msg % contact_detail.value)

        # Verify the correct contact detail type has been passed.
        if contact_detail.type != self.medium:
            msg = "'%s' only supports messages of type %r"
            raise ValueError(msg % (self.__class__, self.medium))

    def send_message(self, attempt):
        """ """
        raise NotImplementedError()
