
class Email:

    def __init__(self, sender, to, reply_to, subject, body):
        self._sender = sender
        self._to = to
        self._reply_to = reply_to
        self._subject = subject
        self._body = body

    @property
    def body(self):
        return self._body

    @property
    def subject(self):
        return self._subject

    @property
    def sender(self):
        return self._sender

    @property
    def to(self):
        return self._to

    @property
    def reply_to(self):
        return self._reply_to
