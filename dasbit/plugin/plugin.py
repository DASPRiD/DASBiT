class Plugin:
    def __init__(self, client):
        self.client = client

        client.registerCommand('plugin', 'enable', 'plugin-enable', '[a-z]+', self.enable)
        client.registerCommand('plugin', 'disable', 'plugin-enable', '[a-z]+', self.disable)

    def enable(self, source, plugin):
        self.client.enablePlugin(plugin)
        self.client.reply(source, 'Plugin %s has been enabled' % plugin)

    def disable(self, source, plugin):
        self.client.disablePlugin(plugin)
        self.client.reply(source, 'Plugin %s has been disabled' % plugin)