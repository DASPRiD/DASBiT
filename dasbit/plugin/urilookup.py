import re
import os
import lxml.html
from urllib import urlencode
from twisted.web.client import getPage
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
            getPage(uri).addCallbacks(
                callback = self._successResult,
                errback = self._errorResult,
                callbackArgs = (message, uri),
                errbackArgs = (message, uri)
            )
                
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
        self._prepareResult(uri, 'Not found', message)
        
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

