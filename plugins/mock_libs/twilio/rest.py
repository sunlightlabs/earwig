from twilio import TwilioRestException


class FakeRestEndpoint(object):
    def create(self, *args, **kwargs):
        if 'to' not in kwargs:
            raise TypeError("Need a to number")

        if 'from_' not in kwargs:
            raise TypeError("Need a from number")

        if kwargs.get('to', None) == 'bad':
            raise TwilioRestException("Bad to")

        return True


class TwilioRestClient(object):
    messages = FakeRestEndpoint()
