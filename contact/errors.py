

class ContactError(Exception):
    pass


class InvalidContactValue(ContactError):
    pass


class Blacklisted(ContactError):
    pass
