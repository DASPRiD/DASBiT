import sys
import os
import json

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
        configPath = os.path.join(self._dataPath, 'config')

        if not os.path.exists(configPath):
            config = self._runConfigPrompt(configPath)
        else:
            fp = open(configPath, 'r')
            config = json.load(fp)
            fp.close()

        self._dispatch(config)

    def _runConfigPrompt(self, configPath):
        print "Initial setup required."

        while True:
            hostname = raw_input('Hostname: ')

            if hostname:
                break

        port          = raw_input('Port [6667]: ')
        nickname      = raw_input('Nickname [DASBiT]: ')
        username      = raw_input('Username [dasbit]: ')
        commandPrefix = raw_input('Command prefix [!]: ')

        if not port:
            port = 6667
        else:
            port = int(port)

        if not nickname:
            nickname = 'DASBiT'

        if not username:
            username = 'dasbit'

        if not commandPrefix:
            commandPrefix = '!'

        config = {
            'hostname':      hostname,
            'port':          port,
            'nickname':      nickname,
            'username':      username,
            'commandPrefix': commandPrefix
        }

        fp = open(configPath, 'w')
        json.dump(config, fp)
        fp.close()

        return config

    def _dispatch(self, config):
        print config


"""
config = ConfigParser()
config.read('config.ini')

factory = IrcFactory()
factory.config = config

reactor.connectTCP(config.get('connection', 'hostname'), config.getint('connection', 'port'), factory)
reactor.run()
"""