from twisted.web.client import getPage
from urllib import urlencode
import json

class Lastfm:
    apiKey = '0bd4c427dcd23f74240d68bd231bd113'
    secret = '9ccf8346c5558fba99307f1137fdd5ef'

    def __init__(self, manager):
        self.client = manager.client

        manager.registerCommand('lastfm', 'now-playing', 'now-playing', '(?P<user>.*?)', self.nowPlaying)

    def nowPlaying(self, source, user):
        if len(user) == 0:
            user = source.prefix['nickname']

        url = 'http://ws.audioscrobbler.com/2.0/?%s' % urlencode({
            'method':  'user.getrecenttracks',
            'user':    user,
            'limit':   '1',
            'api_key': self.apiKey,
            'format':  'json'
        })

        getPage(url).addCallback(self._returnResult, source, user)

    def _returnResult(self, value, source, user):
        try:
            data = json.loads(value)
        except:
            self.client.reply(source, 'An error occured while processing the result', 'notice')
            return

        try:
            for track in data['recenttracks']['track']:
                if track['@attr']['nowplaying'] == 'true':
                    artist = track['artist']['#text']
                    title  = track['name']
                    album  = track['album']['#text']

                    self.client.reply(source, '%s is currently playing %s - %s (%s)' % (user, artist, title, album))
                    return
        except:
            pass

        self.client.reply(source, '%s is currently not playing any song' % user)

