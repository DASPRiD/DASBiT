import os
from dasbit.core import Config

class Channel:
    help = 'https://github.com/DASPRiD/DASBiT/wiki/Channel-Plugin'

    def __init__(self, manager):
        self.client = manager.client
        self.config = Config(os.path.join(manager.dataPath, 'channel'))

        manager.registerCommand('channel', 'join', 'channel-join', '(?P<channel>[^ ]+)(?: (?P<key>.+))?', self.join)
        manager.registerCommand('channel', 'part', 'channel-part', '(?P<channel>[^ ]+)', self.part)
        manager.registerNumeric('channel', [422, 376], self.connected)
        manager.registerNumeric('channel', [403, 405], self.channelError)

    def join(self, source, channel, key = None):
        self.client.join(channel, key)

        self.config[channel] = key
        self.config.save()

        self.client.reply(source, 'Joined %s' % channel, 'notice')

    def part(self, source, channel):
        if not channel in self.config:
            self.client.reply(source, 'Not present in channel %s' % channel, 'notice')
            return

        self.client.part(channel)

        del self.config[channel]
        self.config.save()

        self.client.reply(source, 'Parted %s' % channel, 'notice')

    def connected(self, message):
        for channel, key in self.config.iteritems():
            self.client.join(channel, key)

    def channelError(self, message):
        channel = message.args[0]

        if channel in self.config:
            del self.config[channel]
            self.config.save()
