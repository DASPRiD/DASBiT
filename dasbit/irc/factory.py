from twisted.internet.protocol import ReconnectingClientFactory
from dasbit.irc import Protocol

class Factory(ReconnectingClientFactory):
    def __init__(self, client):
        self.client = client

    def startedConnecting(self, connector):
        self.client.onFactoryStartedConnecting()

    def buildProtocol(self, addr):
        self.client.onFactoryBuildProtocol()
        self.resetDelay()

        return Protocol(self.client)

    def clientConnectionLost(self, connector, reason):
        self.client.onFactoryConnectionLost(reason)
        ReconnectingClientFactory.clientConnectionLost(self, connector, reason)

    def clientConnectionFailed(self, connector, reason):
        self.client.onFactoryConnectionFailed(reason)
        ReconnectingClientFactory.clientConnectionFailed(self, connector, reason)
