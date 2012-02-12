from twisted.internet import reactor
from Queue import PriorityQueue
from time import time
import math
from email.Utils import formatdate
from dasbit.irc import Factory
from dasbit.irc import Ctcp
from dasbit.irc import message as msg
from dasbit.plugin import Manager as PluginManager

class Client:
    def __init__(self, config, dataPath):
        self.config        = config
        self.ctcp          = Ctcp()
        self.pluginManager = PluginManager(self, dataPath)

    def reply(self, source, message, mode = 'normal'):
        if mode == 'normal':
            if source.target == self.config['nickname']:
                target = source.prefix['nickname']
            else:
                target = source.target

            self.sendPrivMsg(target, message)
        elif mode == 'notice':
            self.sendNotice(source.prefix['nickname'], message)

    def join(self, channel, key = None):
        params = [channel]

        if key is not None:
            params.append(key)

        self.send('JOIN', params, 40, 1)

    def part(self, channel):
        self.send('PART', channel, 41, 1)

    def sendPrivMsg(self, target, message):
        self.send('PRIVMSG', [target, message], 11, 0)

    def sendNotice(self, target, message):
        self.send('NOTICE', [target, message], 10, 0)

    def quit(self):
        self.send('QUIT', '', 100, 0)

    def disconnect(self):
        self.transport.loseConnection()

    def send(self, command, params, priority = 0, penalty = 0):
        if self._protocol is None:
            return

        self._sendQueue.put((
            priority,
            (
                math.floor((1 + (len(command) + len(' '.join(params)) + 1) / 100) + penalty),
                command,
                params
            )
        ))

        self._sendQueued(False)

    def handleMessage(self, message):
        self._lastTimeReceived = time()

        if isinstance(message, msg.Ping):
            self.send('PONG', message.server, 110, 1)
        elif isinstance(message, msg.PrivMsg) or isinstance(message, msg.Notice):
            parts = self.ctcp.unpackMessage(message.message)

            for part in parts:
                if isinstance(part, str):
                    if isinstance(part, msg.PrivMsg):
                        if len(parts) == 1:
                            part = message
                        else:
                            part = msg.PrivMsg(message.prefix, message.command, part)

                        self._handlePrivMsg(part)
                    elif isinstance(message, msg.Notice):
                        if len(parts) == 1:
                            part = message
                        else:
                            part = msg.Notice(message.prefix, message.command, part)

                        self._handleNotice(part)
                else:
                    self._handleCtcp(message.prefix['nickname'], part)
        elif isinstance(message, msg.Numeric):
            self._handleNumeric(message)
            pass

    def _handlePrivMsg(self, message):
        pass

    def _handleNotice(self, message):
        pass

    def _handleNumeric(self, message):
        pass

    def _handleCtcp(self, nickname, ctcp):
        (tag, data) = ctcp

        if tag == 'VERSION':
            self.sendNotice(
                nickname,
                self.ctcp.packMessage([('VERSION', 'DASBiT 6.0.0')])
            )
        elif tag == 'PING':
            self.sendNotice(
                nickname,
                self.ctcp.packMessage([('PING', data)])
            )
        elif tag == 'CLIENTINFO':
            self.sendNotice(
                nickname,
                self.ctcp.packMessage([('CLIENTINFO', 'PING VERSION TIME CLIENTINFO')])
            )
        elif tag == 'TIME':
            self.sendNotice(
                nickname,
                self.ctcp.packMessage([('TIME', formatdate())])
            )
        elif tag == 'ACTION':
            # Not really a CTCP request
            pass
        else:
            self.sendNotice(
                nickname,
                self.ctcp.packMessage([('ERRMSG', 'Unknown request')])
            )

    def _sendQueued(self, raisePenalty = True):
        if raisePenalty:
            self._sendPenalty = min(10, self._sendPenalty + 1)

        while self._sendPenalty > 0 and not self._sendQueue.empty():
            (priority, (penalty, command, params)) = self._sendQueue.get()

            self._sendPenalty -= penalty
            self._protocol.send(command, params)

        self._sendDelayedCall = reactor.callLater(1, self._sendQueued)

    def _checkForLag(self):
        if self._lastTimeReceived + 300 <= time():
            print 'Maximum lag reached, closing connection'
            self.disconnect()

        self._lagDelayedCall = reactor.callLater(60, self._checkForLag);

    def onProtocolConnectionMade(self, protocol):
        self._protocol         = protocol
        self._lastTimeReceived = time()
        self._sendQueue        = PriorityQueue()
        self._sendPenalty      = 10

        self.send('NICK', self.config['nickname'], 100, 1)
        self.send('USER', [self.config['username'], '-', '-', 'DASBiT'], 100, 1)

        self._lagDelayedCall  = reactor.callLater(60, self._checkForLag);
        self._sendDelayedCall = reactor.callLater(1, self._sendQueued)

    def onProtocolConnectionLost(self):
        self._sendDelayedCall.cancel()
        self._lagDelayedCall.cancel()

        self._protocol  = None
        self._sendQueue = PriorityQueue()

    def onFactoryStartedConnecting(self):
        print 'Started to connect'

    def onFactoryBuildProtocol(self):
        print 'Connected, resetting reconnection delay'

    def onFactoryConnectionLost(self, reason):
        print 'Lost connection.  Reason: ', reason

    def onFactoryConnectionFailed(self, reason):
        print 'Connection failed. Reason: ', reason

    def run(self):
        self.factory = Factory(self)

        reactor.connectTCP(self.config['hostname'], self.config['port'], self.factory)
        reactor.run()

