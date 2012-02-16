import os
from dasbit.core import Config

class Remind:
    def __init__(self, manager):
        self.client = manager.client
        self.config = Config(os.path.join(manager.dataPath, 'remind'))

        manager.registerCommand('remind', 'remind', 'remind', '(?P<nickname>[^ ]+) to (?P<message>.+)', self.remind)
        manager.registerMessage('remind', self.checkReminder)

    def remind(self, source, nickname, message):
        if not nickname in self.config:
            self.config[nickname] = []

        self.config[nickname].append({
            'message': message,
            'from':    source.prefix['nickname']
        })

        self.client.reply(source, 'Reminder stored', 'notice')

    def checkReminder(self, message):
        if not message.prefix['nickname'] in self.config:
            return

        nickname = message.prefix['nickname']

        for reminder in self.config[nickname]:
            self.client.reply(
                message,
                '%s, %s wants me to remind you to %s' % (
                    nickname, reminder['from'], reminder['message']
                )
            )

        del self.config[nickname]