import os
from twisted.web.client import getPage
from urllib import urlencode
import json
from dasbit.core import Config

class Manual:
    def __init__(self, manager):
        self.client = manager.client
        self.config = Config(os.path.join(manager.dataPath, 'manual'))

        manager.registerCommand('manual', 'set', 'manual-set', '(?P<channel>[^ ]+) (?P<url>[^ ]+)', self.setManualUrl)
        manager.registerCommand('manual', 'search', 'manual', '(?P<query>.*?)(?: for (?P<nickname>.+))?', self.search)

    def setManualUrl(self, source, channel, url):
        self.config[channel] = url
        self.config.save()

        self.client.reply(source, 'Manual URL has been set', 'notice')

    def search(self, source, query, nickname = None):
        if not self.config.has_key(source.target):
            self.client.reply(source, 'No manual URL has been set for this channel', 'notice')
            return

        manualUrl = self.config[source.target]

        params = urlencode({
            'v': '1.0',
            'q': query + ' site:' + manualUrl
        })

        url = 'http://ajax.googleapis.com/ajax/services/search/web?' + params

        if nickname is None:
            nickname = source.prefix['nickname']

        getPage(url).addCallback(self._returnResult, source, nickname)

    def _returnResult(self, value, source, nickname):
        try:
            data = json.loads(value)
        except:
            self.client.reply(source, 'An error occured while processing the result', 'notice')
            return

        if not data.has_key('responseData') or \
            not data['responseData'].has_key('results') or \
            len(data['responseData']['results']) == 0:
            self.client.reply(source, 'Nothing found')
        else:
            self.client.reply(source, nickname + ', see ' + data['responseData']['results'][0]['url'])


