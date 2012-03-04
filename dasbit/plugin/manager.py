import os.path
import pkgutil
import inspect
import re
import dasbit.plugin
from twisted.internet import defer
from twisted.internet import reactor

class Manager:
    def __init__(self, client, dataPath):
        self.client        = client
        self.dataPath      = dataPath
        self.plugins       = {}
        self.commands      = {}
        self.numericEvents = []
        self.messageEvents = {}

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

        if 'plugins' in client.config:
            for plugin, enabled in client.config['plugins'].iteritems():
                if plugin in self.plugins:
                    self.plugins[plugin]['enabled'] = enabled
        else:
            client.config['plugins'] = {}

        self.plugins['plugin']['enabled'] = True
        self.plugins['user']['enabled'] = True
        self.plugins['help']['enabled'] = True

    def enablePlugin(self, plugin):
        if plugin in self.plugins:
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
        if plugin in ['plugin', 'user', 'help']:
            return (False, 'Plugin %s cannot be disabled' % plugin)

        if plugin in self.plugins:
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
            'arguments':  re.compile('^' + arguments + '$') if arguments is not None else None,
            'callback':   callback
        }

    def registerNumeric(self, plugin, events, callback):
        self.numericEvents.append({
            'plugin':   plugin,
            'events':   events if isinstance(events, list) else [events],
            'callback': callback
        })

    def registerMessage(self, plugin, callback):
        self.messageEvents[plugin] = callback

    def registerInterval(self, plugin, interval, callback):
        reactor.callLater(interval, self._intervalCallback, plugin, interval, callback)

    def _intervalCallback(self, plugin, interval, callback):
        if not self.plugins[plugin]['enabled']:
            return

        callback()

        reactor.callLater(interval, self._intervalCallback, plugin, interval, callback)

    def testMessage(self, message):
        self._testMessageForCommand(message)

        for plugin, callback in self.messageEvents.iteritems():
            if not self.plugins[plugin]['enabled']:
                continue

            callback(message)

    def testNumericEvent(self, message):
        for event in self.numericEvents:
            if not self.plugins[event['plugin']]['enabled']:
                continue

            if message.command in event['events']:
                event['callback'](message)

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

        if not command in self.commands:
            commandMatches = []
            for commandName in self.commands:
                if commandName.startswith(command) \
                    and self.plugins[self.commands[commandName]['plugin']]['enabled']:
                    commandMatches.append(commandName)

            if len(commandMatches) > 1:
                self.client.reply(message, 'Ambiguous command: !{0}. Try !{1}'.format(command, ', !'.join(commandMatches)), 'notice')
                return
            
            if len(commandMatches) == 1:
                command = commandMatches[0]

        if command in self.commands:
            command = self.commands[command]

            if not self.plugins[command['plugin']]['enabled']:
                return

            if command['permission'] is not None:
                d = defer.maybeDeferred(
                    self.plugins['user']['instance'].verifyAccess,
                    message,
                    command['plugin'] + '.' + command['permission']
                )
                d.addCallback(self._executeCommand, message, command, arguments)
            else:
                self._executeCommand(True, message, command, arguments)

    def _executeCommand(self, isAllowed, message, command, arguments):
        if not isAllowed:
            self.client.reply(message, 'You are not allowed to use this command', 'notice')
            return

        if command['arguments'] is not None:
            match = command['arguments'].match(arguments)

            if match is None:
                return

            command['callback'](message, **match.groupdict())
        else:
            command['callback'](message)
