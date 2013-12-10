from twilio import TwilioRestException

class FakeRestEndpoint(object):
    def create(self, *args, **kwargs):
        if kwargs.get('to', None) == 'bad':
            raise TwilioRestException("Bad to")
        return True


class TwilioRestClient(object):
    messages = FakeRestEndpoint()
