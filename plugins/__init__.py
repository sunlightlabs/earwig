from contact.errors import CantCancelMessage


class ContactPlugin(object):
    """ """

    def send_message(self, attempt):
        """ """
        raise NotImplementedError()

    def check_message_status(self, attempt):
        """ """
        raise NotImplementedError()
