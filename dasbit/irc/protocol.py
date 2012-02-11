from twisted.internet.protocol import Protocol as BaseProtocol
import re
from dasbit.irc import message

class Protocol(BaseProtocol):
    def __init__(self, client):
        self.client = client
        self.buffer = ''

    def connectionMade(self):
        self.client.onProtocolConnectionMade(self)

    def connectionLost(self, reason):
        self.client.onProtocolConnectionLost()

    def dataReceived(self, data):
        self.buffer += data

        while '\r\n' in self.buffer:
            pos         = self.buffer.find('\r\n')
            line        = self.buffer[0:pos+2]
            self.buffer = self.buffer[pos+2:]

            if line == '\r\n':
                continue

            print '< ' + line.strip()

            self.client.handleMessage(self._parseLine(line.strip()))

    def send(self, command, params):
        message = command

        if isinstance(params, list):
            if len(params) == 0:
                lastParam = ''
            else:
                lastParam = params.pop()

            if len(params) > 0:
                message += ' ' + ' '.join(params)

            message += ' :' + lastParam
        else:
            message += ' :' + params

        message += '\r\n'

        print '> ' + message.strip()

        self.transport.write(message.encode('utf-8'))

    def _parseLine(self, line):
        # General parsing
        if line.startswith(':'):
            parts   = re.split('[ ]+', line.strip(), 2)
            prefix  = self._parsePrefix(parts[0][1:])
            command = parts[1]
            rawArgs = parts[2]
        else:
            parts   = re.split('[ ]+', line.strip(), 1)
            prefix  = None
            command = parts[0]
            rawArgs = parts[1]

        # Find arguments
        trailingPos = rawArgs.find(':')

        if trailingPos > -1:
            trailing = rawArgs[trailingPos + 1:]
            rawArgs  = rawArgs[0:trailingPos].strip()
        else:
            trailing = None

        if rawArgs:
            args = re.split('[ ]+', rawArgs)
        else:
            args = []

        if trailing is not None:
            args.append(trailing)

        # Determine message type
        if command.isdigit():
            return message.Numeric(prefix, command, args)
        else:
            command = command.upper()

            if command == 'PRIVMSG':
                return message.PrivMsg(prefix, command, args)
            elif command == 'NOTICE':
                return message.Notice(prefix, command, args)
            elif command == 'PING':
                return message.Ping(prefix, command, args)
            else:
                return message.Generic(prefix, command, args)

    def _parsePrefix(self, prefix):
        try:
            rest, host = prefix.split('@')
        except ValueError:
            return (prefix, None, None)

        try:
            nickname, user = rest.split('!')
        except ValueError:
            return (rest, None, host)

        return (nickname, user, host)
