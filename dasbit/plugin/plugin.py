class Plugin:
    def __init__(self, manager):
        self.manager = manager
        self.client  = manager.client

        manager.registerCommand('plugin', 'enable', 'plugin-enable', '(?P<plugin>[a-z]+)', self.enable)
        manager.registerCommand('plugin', 'disable', 'plugin-disable', '(?P<plugin>[a-z]+)', self.disable)

    def enable(self, source, plugin):
        success, message = self.manager.enablePlugin(plugin)

        if success:
            self.client.reply(source, 'Plugin %s has been enabled' % plugin, 'notice')
        else:
            self.client.reply(source, message, 'notice')

    def disable(self, source, plugin):
        success, message = self.manager.disablePlugin(plugin)

        if success:
            self.client.reply(source, 'Plugin %s has been disabled' % plugin, 'notice')
        else:
            self.client.reply(source, message, 'notice')
