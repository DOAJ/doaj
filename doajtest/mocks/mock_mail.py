from flask_mail import Message


class MockMail:
    def __init__(self, *args, **kwargs):
        self.messages = []

    def send(self, message: Message):
        print('----------- Mock send ----------------')
        print(f'{message.subject=}')
        print(f'{message.date=}')
        print(f'{message.sender=}')
        print(f'{message.recipients=}')
        print(f'message.body: ')
        print(message.body)
        print('---------------------------')
        self.messages.append(message)
