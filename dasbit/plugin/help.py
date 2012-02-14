class Help:
    def __init__(self, manager):
        self.manager = manager
        self.client  = manager.client

        manager.registerCommand('help', None, 'help', '(?P<plugin>[a-z]+)?', self.help)

    def help(self, source, plugin = None):
        if plugin is None:
            pluginNames = []

            for pluginName, data in self.manager.plugins.iteritems():
                if data['enabled']:
                    pluginNames.append(pluginName)

            self.client.reply(source, 'For help about plugins, type !help <plugin>. The available plugins are: %s' % ', '.join(pluginNames), 'notice')
        elif plugin in self.manager.plugins and self.manager.plugins[plugin]['enabled']:
            pluginInstance = self.manager.plugins[plugin]['instance']
            print pluginInstance.__class__.help
            if hasattr(pluginInstance.__class__, 'help'):
                self.client.reply(source, 'Help for plugin %s: %s' % (plugin, pluginInstance.__class__.help), 'notice')
            else:
                self.client.reply(source, 'There is no help available for the plugin %s' % plugin, 'notice')
        else:
            self.client.reply(source, 'There is no plugin with the name %s, see !help for available plugins' % plugin, 'notice')
