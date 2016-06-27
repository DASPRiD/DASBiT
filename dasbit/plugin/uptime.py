import os
import psutil
from time import time
import datetime
from dasbit.helper import timesince

class Uptime:
    def __init__(self, manager):
        self.client = manager.client

        manager.registerCommand('uptime', 'uptime', 'uptime', None, self.getUptime)

    def getUptime(self, source):
        process = psutil.Process(os.getpid())

        self.client.reply(source, 'Uptime: %s' % timesince(datetime.datetime.utcfromtimestamp(process.create_time()), ''))

