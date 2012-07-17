import os
from dasbit.core import Config
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
                    nickname, reminder['from'], reminder['message'], self._timesince(date)
                )
            )

        del self.config[nickname]
        self.config.save()

    def _timesince(self, date):
        chunks = (
            (60 * 60 * 24 * 365, lambda n: 'year' if n is 1 else 'years'),
            (60 * 60 * 24 * 30, lambda n: 'month' if n is 1 else 'months'),
            (60 * 60 * 24 * 7, lambda n: 'week' if n is 1 else 'weeks'),
            (60 * 60 * 24, lambda n: 'day' if n is 1 else 'days'),
            (60 * 60, lambda n: 'hour' if n is 1 else 'hours'),
            (60, lambda n: 'minute' if n is 1 else 'minutes')
        )

        now   = datetime.datetime.utcnow()
        delta = now - date
        since = delta.days * 24 * 60 * 60 + delta.seconds

        if since <= 0:
            return '0 minutes ago'

        for i, (seconds, name) in enumerate(chunks):
            count = since // seconds

            if count != 0:
                break

        s = '%d %s' % (count, name(count))

        if i + 1 < len(chunks):
            seconds2, name2 = chunks[i + 1]
            count2 = (since - (seconds * count)) // seconds2

            if count2 != 0:
                s += ' and %d %s' % (count2, name2(count2))

        s += ' ago'

        return s
