import os.path
import pkgutil
import inspect
import re
import dasbit.plugin

class Manager:
    def __init__(self, client, dataPath):
        self.client   = client
        self.dataPath = dataPath
        self.plugins  = {}
        self.commands = {}

        packagePath = os.path.dirname(dasbit.plugin.__file__)

        for _, name, _ in pkgutil.iter_modules([packagePath]):
            if name == 'manager':
                continue

            module = __import__('dasbit.plugin.' + name, globals(), locals(), ['*'], -1)

            for objectName, object in inspect.getmembers(module):
                if inspect.isclass(object) and objectName.lower() == name:
                    self.plugins[name] = {
                        'instance': object(self),
                        'enabled':  False
                    }

        if client.config.has_key('plugins'):
            for plugin, enabled in client.config['plugins'].iteritems():
                if self.plugins.has_key(plugin):
                    self.plugins[plugin]['enabled'] = enabled
        else:
            client.config['plugins'] = {}

        self.plugins['plugin']['enabled'] = True
        #self.plugins['user']['enabled'] = True

    def enablePlugin(self, plugin):
        if self.plugins.has_key(plugin):
            if self.plugins[plugin]['enabled']:
                return (False, 'Plugin %s is already enabled' % plugin)
            else:
                self.plugins[plugin]['enabled'] = True
                self.client.config['plugins'][plugin]  = True
                self.client.config.save()
                return (True, None)
        else:
            return (False, 'Plugin %s does not exist' % plugin)

    def disablePlugin(self, plugin):
        if plugin in ['plugin', 'user']:
            return (False, 'Plugin %s cannot be disabled' % plugin)

        if self.plugins.has_key(plugin):
            if not self.plugins[plugin]['enabled']:
                return (False, 'Plugin %s is already disabled' % plugin)
            else:
                self.plugins[plugin]['enabled'] = False
                self.client.config['plugins'][plugin]  = False
                self.client.config.save()
                return (True, None)
        else:
            return (False, 'Plugin %s does not exist' % plugin)

    def registerCommand(self, plugin, permission, command, arguments, callback):
        self.commands[command] = {
            'plugin':     plugin,
            'permission': permission,
            'arguments':  re.compile('^' + arguments + '$'),
            'callback':   callback
        }

    def testMessage(self, message):
        self._testMessageForCommand(message)

    def _testMessageForCommand(self, message):
        if self.client.config['commandPrefix']:
            if message.message.startswith(self.client.config['commandPrefix']):
                content = message.message[len(self.client.config['commandPrefix']):]
            else:
                return
        else:
            content = message.message

        data = content.split(' ', 1)

        if len(data) == 1:
            command   = data[0]
            arguments = ''
        else:
            command   = data[0]
            arguments = data[1]

        if self.commands.has_key(command):
            command = self.commands[command]

            if not self.plugins[command['plugin']]['enabled']:
                return

            # Todo: check for permissions

            if command['arguments'] is not None:
                match = command['arguments'].match(arguments)

                if match is None:
                    return

                command['callback'](message, **match.groupdict())