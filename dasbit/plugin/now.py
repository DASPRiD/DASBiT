import os
import pytz
import datetime
from time import time
from dasbit.core import Config

class Now:
    help = 'https://github.com/DASPRiD/DASBiT/wiki/Now-Plugin'

    def __init__(self, manager):
        self.client = manager.client
        self.config = Config(os.path.join(manager.dataPath, 'now'))

        manager.registerCommand('now', 'time', 'time', '(?P<identifier>[^ ]+)?', self.getTime)
        manager.registerCommand('now', 'time-set', 'time-set', '(?P<timezone>[^ ]+)', self.setTime)

    def setTime(self, source, timezone):
        try:
            tz = pytz.timezone(timezone)
        except pytz.UnknownTimeZoneError:
            self.client.reply(source, '%s is not a valid timezone' % timezone, 'notice')
            return

        self.config[source.prefix['nickname']] = timezone
        self.config.save()

        self.client.reply(source, 'Your timezone has been set', 'notice')

    def getTime(self, source, identifier):
        now = datetime.datetime.fromtimestamp(time(), pytz.utc)

        if identifier:
            if identifier in self.config:
                timezone   = self.config[identifier]
            else:
                timezone   = identifier

            try:
                tz = pytz.timezone(timezone)
            except pytz.UnknownTimeZoneError:
                self.client.reply(source, '%s is not a valid timezone or identifier' % timezone, 'notice')
                return

            now = now.astimezone(tz)
            
            self.client.reply(source, 'Time for %s: %s' % (identifier, now.strftime('%A, %H:%M (%Z%z)')))
        else:
            self.client.reply(source, 'Current time: %s' % now.strftime('%A, %H:%M (%Z%z)'))
