from dasbit.core import Config
from twisted.web.client import getPage
from urllib import urlencode, quote_plus
import os
import base64
import json
import HTMLParser

class Twitter:
    help = 'https://github.com/DASPRiD/DASBiT/wiki/Twitter-Plugin'

    def __init__(self, manager):
        self.client = manager.client
        self.parser = HTMLParser.HTMLParser()
        self.config = Config(os.path.join(manager.dataPath, 'twitter'))

        if not 'aliases' in self.config:
            self.config['aliases'] = {}

        manager.registerCommand('twitter', 'alias', 'alias-twitter', '(?P<handle>[^ ]+)', self.alias)
        manager.registerCommand('twitter', 'authenticate', 'authenticate-twitter', '(?P<key>[a-zA-Z0-9]+) (?P<secret>[a-zA-Z0-9]+)', self.authenticate)
        manager.registerCommand('twitter', 'lookup', 'twitter', '(?P<query>.*?)', self.lookup)

    def alias(self, source, handle):
        self.config['aliases'][source.prefix['nickname']] = handle
        self.config.save()
        self.client.reply(source, 'Alias stored', 'notice')

    def authenticate(self, source, key, secret):
        bearerTokenCredentials = base64.b64encode('%s:%s' % (quote_plus(key), quote_plus(secret)))

        getPage(
            'https://api.twitter.com/oauth2/token',
            method = 'POST',
            postdata = 'grant_type=client_credentials',
            headers = {
                'Authorization' : 'Basic %s' % bearerTokenCredentials,
                'Content-Type'  : 'application/x-www-form-urlencoded;charset=UTF-8'
            }
        ).addCallback(self._authenticate, source).addErrback(self._error, source)

    def _error(self, failure, source):
        value = failure.value.response

        try:
            data = json.loads(value)
        except:
            self.client.reply(source, 'An error occured while processing the response', 'notice')
            return

        if 'errors' in data:
            self.client.reply(source, 'API failure: %s' % data['errors'][0]['message'], 'notice')
            return

    def _authenticate(self, value, source):
        try:
            data = json.loads(value)
        except:
            self.client.reply(source, 'An error occured while processing the authentication', 'notice')
            return

        if not 'token_type' in data:
            self.client.reply(source, 'Missing token type in authentication response', 'notice')
            return

        if not 'access_token' in data:
            self.client.reply(source, 'Missing access_token in authentication response', 'notice')
            return

        if data['token_type'] != 'bearer':
            self.client.reply(source, 'Returned token type is not bearer', 'notice')
            return

        self.config['access_token'] = data['access_token']
        self.config.save()

        self.client.reply(source, 'Authentication succeeded', 'notice')

    def lookup(self, source, query):
        if not 'access_token' in self.config:
            self.client.reply(source, 'Twitter plugin not authenticated yet', 'notice')
            return

        if query.isdigit():
            url = 'https://api.twitter.com/1.1/statuses/show/%s.json' % query
        elif len(query) > 0:
            url = 'https://api.twitter.com/1.1/users/show.json?%s' % urlencode({'screen_name' : query})
        else:
            if source.prefix['nickname'] in self.config['aliases']:
                handle = self.config['aliases'][source.prefix['nickname']]
            else:
                handle = source.prefix['nickname']

            url = 'https://api.twitter.com/1.1/users/show.json?%s' % urlencode({'screen_name' : handle})

        getPage(
            url,
            method = 'GET',
            headers = {'Authorization' : 'Bearer %s' % self.config['access_token']}
        ).addCallback(self._returnResult, source, query.isdigit()).addErrback(self._error, source)

    def _returnResult(self, value, source, isNumericLookup):
        try:
            data = json.loads(value)
        except:
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

        text = self.parser.unescape(text).replace('\n', ' ').replace('\r', '')

        url = 'https://twitter.com/#!/%s/status/%s' % (user, id)

        self.client.reply(source, '<%s> %s (%s)' % (user, text, url))


