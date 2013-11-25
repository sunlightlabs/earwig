

class ContactError(Exception):
    """ """
    pass


class CantCancelMessage(ContactError):
    """ """
    pass


class InvalidContactType(ContactError):
    pass


class InvalidContactValue(ContactError):
    pass


class Blacklisted(ContactError):
    pass