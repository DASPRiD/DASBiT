import sys
import os
from dasbit.core import Config
from dasbit.irc import Client

class Frontend:
    def run(self):
        # Get data path and validate it
        if len(sys.argv) < 2:
            print "Expected data path as first argument"
            sys.exit(2)

        self._dataPath = sys.argv[1]

        if not os.path.exists(self._dataPath):
            print "Data path does not exist"
            sys.exit(2)

        if not os.path.isdir(self._dataPath):
            print "Data path is not a directory"
            sys.exit(2)

        # Check for configuration
        config = Config(os.path.join(self._dataPath, 'config'))

        if not 'hostname' in config:
            config = self._runConfigPrompt(config)

        self._dispatch(config)

    def _runConfigPrompt(self, config):
        print "Initial setup required."

        if sys.version_info[0] >= 3:
            get_input = input
        else:
            get_input = raw_input

        while True:
            config['hostname'] = get_input('Hostname: ')

            if config['hostname']:
                break

        config['port']          = get_input('Port [6667]: ')
        config['nickname']      = get_input('Nickname [DASBiT]: ')
        config['username']      = get_input('Username [dasbit]: ')
        config['commandPrefix'] = get_input('Command prefix [!]: ')

        if not config['port']:
            config['port'] = 6667
        else:
            config['port'] = int(config['port'])

        if not config['nickname']:
            config['nickname'] = 'DASBiT'

        if not config['username']:
            config['username'] = 'dasbit'

        if not config['commandPrefix']:
            config['commandPrefix'] = '!'

        config.save()

        return config

    def _dispatch(self, config):
        client = Client(config, self._dataPath)
        client.run()
