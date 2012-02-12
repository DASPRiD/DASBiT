import os.path
import pkgutil
import inspect
import re
import dasbit.plugin

class Manager:
    def __init__(self, client):
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
                        'instance': object(self, client),
                        'enabled':  False
                    }

        self.plugins['plugin']['enabled'] = True
        #self.plugins['user']['enabled'] = True

    def enablePlugin(self, plugin):
        if self.plugins.has_key(plugin):
            if self.plugins[plugin]['enabled']:
                return (False, 'Plugin %s is already enabled' % plugin)
            else:
                self.plugins[plugin]['enabled'] = True
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
