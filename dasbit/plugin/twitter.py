from twisted.web.client import getPage
from urllib import urlencode
import json

class Twitter:
    def __init__(self, manager):
        self.client = manager.client

        manager.registerCommand('twitter', 'lookup', 'twitter', '(?P<query>.*?)', self.lookup)

    def lookup(self, source, query):
        if query.isdigit():
            url = 'http://api.twitter.com/1/statuses/show/%s.json' % query
        elif len(query) > 0:
            url = 'http://api.twitter.com/1/users/show.json?%s' % urlencode({'screen_name' : query})
        else:
            url = 'http://api.twitter.com/1/users/show.json?%s' % urlencode({'screen_name' : source.prefix['nickname']})

        getPage(url).addCallback(self._returnResult, source, query.isdigit())

    def _returnResult(self, value, source, isNumericLookup):
        try:
            data = json.loads(value)
        except:
            self.client.reply(source, 'An error occured while processing the result', 'notice')
            return

        if 'error' in data:
            self.client.reply(source, 'An error occured while processing the result', 'notice')
            return

        if isNumericLookup:
            user = data['user']['screen_name']
            text = data['text']
            id   = data['id_str']
        else:
            user = data['screen_name']
            text = data['status']['text']
            id   = data['status']['id_str']

        url = 'https://twitter.com/#!/%s/status/%s' % (user, id)

        self.client.reply(source, '<%s> %s (%s)' % (user, text, url))


