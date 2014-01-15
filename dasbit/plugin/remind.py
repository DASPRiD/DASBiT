import os
from dasbit.core import Config
from dasbit.helper import timesince
from time import time
import datetime

class Remind:
    def __init__(self, manager):
        self.client = manager.client
        self.config = Config(os.path.join(manager.dataPath, 'remind'))

        manager.registerCommand('remind', 'remind', 'remind', '(?P<nickname>[^ ]+) (in (?P<channel>[^ ]+) )?(?P<message>(?:to|about|that) .+)', self.remind)
        manager.registerMessage('remind', self.checkReminder)

    def remind(self, source, nickname, channel, message):
        if not nickname in self.config:
            self.config[nickname] = []

        self.config[nickname].append({
            'message': message,
            'channel': None if channel == None else channel.lower(),
            'from':    source.prefix['nickname'],
            'time':    time()
        })
        self.config.save()

        self.client.reply(source, 'Reminder stored', 'notice')

    def checkReminder(self, message):
        if not message.prefix['nickname'] in self.config:
            return

        nickname = message.prefix['nickname']
        unsent   = []

        for reminder in self.config[nickname]:
            # Fallbacks for old reminders
            if not 'channel' in reminder:
                channel = None
            else:
                channel = reminder['channel']

            if not 'time' in reminder:
                date = datetime.datetime.utcnow()
            else:
                date = datetime.datetime.utcfromtimestamp(reminder['time'])

            if channel != None and channel != message.target.lower():
                unsent.append(reminder)
                continue

            self.client.reply(
                message,
                '%s, %s wants me to remind you %s (written %s)' % (
                    nickname, reminder['from'], reminder['message'], timesince(date)
                )
            )

        if len(unsent) > 0:
            self.config[nickname] = unsent
        else:
            del self.config[nickname]

        self.config.save()
