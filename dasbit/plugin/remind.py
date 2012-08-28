import os
from dasbit.core import Config
from dasbit.helper import timesince
from time import time
import datetime

class Remind:
    def __init__(self, manager):
        self.client = manager.client
        self.config = Config(os.path.join(manager.dataPath, 'remind'))

        manager.registerCommand('remind', 'remind', 'remind', '(?P<nickname>[^ ]+) (?P<message>(?:to|about|that) .+)', self.remind)
        manager.registerMessage('remind', self.checkReminder)

    def remind(self, source, nickname, message):
        if not nickname in self.config:
            self.config[nickname] = []

        self.config[nickname].append({
            'message': message,
            'from':    source.prefix['nickname'],
            'time':    time()
        })
        self.config.save()

        self.client.reply(source, 'Reminder stored', 'notice')

    def checkReminder(self, message):
        if not message.prefix['nickname'] in self.config:
            return

        nickname = message.prefix['nickname']

        for reminder in self.config[nickname]:
            # Fallback for old reminders
            if not 'time' in reminder:
                date = datetime.datetime.utcnow()
            else:
                date = datetime.datetime.utcfromtimestamp(reminder['time'])

            self.client.reply(
                message,
                '%s, %s wants me to remind you %s (written %s)' % (
                    nickname, reminder['from'], reminder['message'], timesince(date)
                )
            )

        del self.config[nickname]
        self.config.save()
