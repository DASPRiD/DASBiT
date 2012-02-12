from twisted.web.client import getPage
from urllib import urlencode
import json

class Manual:
    def __init__(self, manager):
        self.client = manager.client

        manager.registerCommand('manual', 'search', 'manual', '(?P<query>.*?)(?: for (?P<nickname>.+))?', self.search)

    def search(self, source, query, nickname = None):
        params = urlencode({
            'v': '1.0',
            'q': query + ' site:http://framework.zend.com/manual/en/'
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


