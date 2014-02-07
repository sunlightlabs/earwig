
def connect_to_region():
    return Connection()


class Connection(object):
    def send_email(self, source, subject, body, to_addresses, reply_addresses):
        return {
            'SendEmailResponse': {
                'ResponseMetadata': {
                    'RequestID': 'cow_id'
                    },
                },
            'SendEmailResult': {
                'MessageId': 'message_id'
                }
            }

