import os
from dasbit.core import Config
from dasbit.helper import timesince
from time import time
import datetime

class Seen:
    help = 'https://github.com/DASPRiD/DASBiT/wiki/Seen-Plugin'

    def __init__(self, manager):
        self.client = manager.client
        self.config = Config(os.path.join(manager.dataPath, 'seen'))

        manager.registerCommand('seen', 'seen', 'seen', '(?P<nickname>[^ ]+)', self.check)
        manager.registerMessage('seen', self.record)

    def check(self, source, nickname):
        if not nickname in self.config:
            self.client.reply(source, 'I have never seen %s' % nickname)

        if isinstance(self.config[nickname], dict):
            self.client.reply(source, '%s was last seen %s in %s' % (
                nickname,
                timesince(datetime.datetime.utcfromtimestamp(self.config[nickname]['time'])),
                self.config[nickname]['channel']
            ))
        else:
            self.client.reply(source, '%s was last seen %s' % (
                nickname,
                timesince(datetime.datetime.utcfromtimestamp(self.config[nickname]))
            ))

    def record(self, message):
        self.config[message.prefix['nickname']] = {
            'channel': message.target,
            'time':    time()
        }
        self.config.save()

