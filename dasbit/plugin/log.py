import os
import time
import struct
from dasbit.core import Config

class Log:
    def __init__(self, manager):
        self.client  = manager.client
        self.config  = Config(os.path.join(manager.dataPath, 'log'))
        self.logs    = {}
        self.logPath = os.path.join(manager.dataPath, 'logs')

        if not os.path.exists(self.logPath):
            os.mkdir(self.logPath)

        manager.registerCommand('log', 'enable', 'log-enable', '(?P<channel>[^ ]+)', self.enable)
        manager.registerCommand('log', 'disable', 'log-disable', '(?P<channel>[^ ]+)', self.disable)
        manager.registerMessage('log', self.logMessage)

    def enable(self, source, channel):
        self.config[channel] = True
        self.config.save()

        self.client.reply(source, 'Logging has been enabled for %s' % channel, 'notice')

    def disable(self, source, channel):
        if not channel in self.config:
            self.client.reply(source, 'Logging is not enabled for %s' % channel, 'notice')
            return

        del self.config[channel]
        self.config.save()

        if channel in self.logs:
            self.logs[channel]['fp'].close()
            del self.logs[channel]

        self.client.reply(source, 'Logging has been disabled for %s' % channel, 'notice')

    def logMessage(self, message):
        if not message.target in self.config:
            return

        channel   = message.target
        now       = time.time()
        nowStruct = time.gmtime(now)
        date      = time.strftime('%Y-%m-%d', nowStruct)

        if not channel in self.logs:
            self.logs[channel] = {
                'date': date,
                'fp':   None
            }
        elif self.logs[channel]['date'] != date:
            self.logs[channel]['fp'].close()
            self.logs[channel]['fp']   = None
            self.logs[channel]['date'] = date

        if self.logs[channel]['fp'] is None:
            channelPath = os.path.join(self.logPath, channel)
            yearPath    = os.path.join(channelPath, time.strftime('%Y', nowStruct))
            monthPath   = os.path.join(yearPath, time.strftime('%m', nowStruct))
            dayPath     = os.path.join(monthPath, time.strftime('%d', nowStruct))

            if not os.path.exists(channelPath):
                os.mkdir(channelPath)

            if not os.path.exists(yearPath):
                os.mkdir(yearPath)

            if not os.path.exists(monthPath):
                os.mkdir(monthPath)

            self.logs[channel]['fp'] = open(dayPath, 'ab')

        self.logs[channel]['fp'].write(struct.pack(
            '<LB',
            int(now),
            len(message.prefix['nickname'])
        ) + message.prefix['nickname'] + struct.pack(
            '<H',
            len(message.message)
        ) + message.message)
