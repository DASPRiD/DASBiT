from __future__ import absolute_import
import pytz
import datetime
from time import time

class Time:
    def __init__(self, manager):
        self.client = manager.client

        manager.registerCommand('time', 'time', 'time', '(?P<timezone>[^ ]+)?', self.getTime)

    def getTime(self, source, timezone):
        now = datetime.datetime.fromtimestamp(time(), pytz.utc)

        if timezone:
            try:
                tz = pytz.timezone(timezone)
            except pytz.UnknownTimeZoneError:
                self.client.reply(source, '%s is not a valid timezone' % timezone, 'notice')
                return

            now = now.astimezone(tz)

        self.client.reply(source, now.strftime('%Y-%m-%d %H:%M:%S %Z%z'))

