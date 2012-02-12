class Plugin:
    def __init__(self, manager, client):
        self.client = client

        manager.registerCommand('plugin', 'enable', 'plugin-enable', '(?P<plugin>[a-z]+)', self.enable)
        manager.registerCommand('plugin', 'disable', 'plugin-enable', '(?P<plugin>[a-z]+)', self.disable)

    def enable(self, source, plugin):
        success, message = self.client.enablePlugin(plugin)

        if success:
            self.client.reply(source, 'Plugin %s has been enabled' % plugin, 'notice')
        else:
            self.client.reply(source, message, 'notice')

    def disable(self, source, plugin):
        success, message = self.client.disablePlugin(plugin)

        if success:
            self.client.reply(source, 'Plugin %s has been disabled' % plugin, 'notice')
        else:
            self.client.reply(source, message, 'notice')
