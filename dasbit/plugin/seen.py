import os
from dasbit.core import Config
from dasbit.helper import timesince
from time import time
import datetime

class Seen:
    def __init__(self, manager):
        self.client = manager.client
        self.config = Config(os.path.join(manager.dataPath, 'seen'))

        manager.registerCommand('seen', 'seen', 'seen', '(?P<nickname>[^ ]+)', self.check)
        manager.registerMessage('seen', self.record)

    def check(self, source, nickname):
        if not nickname in self.config:
            self.client.reply(source, 'I have never seen %s' % nickname)

        self.client.reply(source, '%s was last seen %s' % (nickname, timesince(datetime.datetime.utcfromtimestamp(self.config[nickname]))))

    def record(self, message):
        self.config[message.prefix['nickname']] = time()
        self.config.save()

