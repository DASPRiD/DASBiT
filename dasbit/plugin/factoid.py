import os
from dasbit.core import Config

class Factoid:
    def __init__(self, manager):
        self.client = manager.client
        self.config = Config(os.path.join(manager.dataPath, 'factoid'))

        manager.registerCommand('factoid', 'add', 'factoid-add', '(?:(?P<channel>#[^ ]+) )?(?P<key>.+?) => (?P<value>.+?)', self.add)
        manager.registerCommand('factoid', 'remove', 'factoid-remove', '(?:(?P<channel>#[^ ]+) )?(?P<key>.+?)', self.remove)
        manager.registerCommand('factoid', 'tell', 'tell', '(?P<nickname>[^ ]+) about (?P<key>.+)', self.tell)

    def tell(self, source, nickname, key):
        channel = source.target.lower()
        key     = key.lower()

        if channel in self.config and \
            key in self.config[channel]:
            value = self.config[channel][key]
        elif 'global' in self.config and \
            key in self.config['global']:
            value = self.config['global'][key]
        else:
            self.client.reply(source, 'Factoid "%s" not found' % key, 'notice')
            return

        self.client.reply(source, '%s, %s' % (nickname, value))

    def add(self, source, key, value, channel = None):
        if channel is None:
            group = 'global'
        else:
            group = channel.lower()

        key = key.lower()

        if not group in self.config:
            self.config[group] = {}

        self.config[group][key] = value
        self.config.save()

        self.client.reply(source, 'Factoid "%s" has been added to %s' % (key, group), 'notice')

    def remove(self, source, key, channel = None):
        if channel is None:
            group = 'global'
        else:
            group = channel.lower()

        key = key.lower()

        if not group in self.config or \
            not key in self.config[group]:
            self.client.reply(source, 'Factoid "%s" not found in %s' % (key, group), 'notice')
            return

        del self.config[group][key]
        self.config.save()

        self.client.reply(source, 'Factoid "%s" has been removed from %s' % (key, group), 'notice')
