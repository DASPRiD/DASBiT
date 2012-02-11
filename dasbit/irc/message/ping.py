from dasbit.irc.message import Generic

class Ping(Generic):
    def __init__(self, prefix, command, args):
        Generic.__init__(self, prefix, command, args)

        self.server = args[0]
        