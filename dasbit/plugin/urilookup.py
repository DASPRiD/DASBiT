import re
import os
import lxml.html
from urllib import urlencode
import treq
from twisted.internet.defer import Deferred
from twisted.web.client import getPage
from twisted.web.client import ResponseDone
from twisted.web.http import PotentialDataLoss
from twisted.internet.protocol import Protocol
from dasbit.core import Config

class UriLookup:
    def __init__(self, manager):
        self.client  = manager.client
        self.config  = Config(os.path.join(manager.dataPath, 'log'))

        manager.registerCommand('urilookup', 'enable', 'urilookup-enable', '(?P<channel>[^ ]+)', self.enable)
        manager.registerCommand('urilookup', 'disable', 'urilookup-disable', '(?P<channel>[^ ]+)', self.disable)
        manager.registerMessage('urilookup', self.lookupUri)

    def enable(self, source, channel):
        self.config[channel] = True
        self.config.save()

        self.client.reply(source, 'URI lookup has been enabled for %s' % channel, 'notice')

    def disable(self, source, channel):
        if not channel in self.config:
            self.client.reply(source, 'URI lookup is not enabled for %s' % channel, 'notice')
            return

        del self.config[channel]
        self.config.save()

        self.client.reply(source, 'URI lookup has been disabled for %s' % channel, 'notice')

    def lookupUri(self, message):
        if not message.target in self.config:
            return

        for uri in re.findall("https?://[^\s]+", message.message):
            treq.get(uri, unbuffered = True).addCallbacks(
                callback = self._gotResponse,
                errback = self._errorResult,
                callbackArgs = (message, uri),
                errbackArgs = (message, uri)
            )
            
    def _gotResponse(self, response, message, uri):
        if response.headers.hasHeader('content-type'):
            mimeType = response.headers.getRawHeaders('content-type')[0].split(';')[0].strip().lower()

            if mimeType == 'text/html':
                d = Deferred()
                d.addCallbacks(
                    callback = self._successResult,
                    callbackArgs = (message, uri)
                )

                response.deliverBody(_BodyCollector(d))
                return

            self._prepareResult(uri, mimeType, message)
            return

        self._prepareResult(uri, 'Unknown', message)
                
    def _successResult(self, html, message, uri):
        tree         = lxml.html.fromstring(html)
        titleElement = tree.find('./head/title')
        
        if titleElement == None:
            title = 'Undefined'
        else:
            title = titleElement.text
            
        title = (title[:40] + '...') if len(title) > 40 else title

        self._prepareResult(uri, title, message)

    def _errorResult(self, error, message, uri):
        self._prepareResult(uri, 'Error retrieving URI', message)
        
    def _prepareResult(self, uri, title, message):
        if len(uri) > 25:
            apiUri = 'http://tinyurl.com/api-create.php?%s' % urlencode({
                'url': uri
            })
                        
            getPage(apiUri).addCallback(self._returnResult, title, message)
        else:
            self._returnResult(uri, title, message)
                    
    def _returnResult(self, uri, title, message):
        self.client.reply(message, '[ %s ] %s' % (uri, title))

# We gotta make sure to not download huge files; the first 100kb should usually
# be enough to find the title.
class _BodyCollector(Protocol):
    def __init__(self, finished):
        self.finished = finished
        self.size     = 0
        self.data     = ''

    def dataReceived(self, data):
        self.data += data
        self.size += len(data)

        if self.size > 1024 * 100:
            self.loseConnection()

    def connectionLost(self, reason):
        self.finished.callback(self.data)

