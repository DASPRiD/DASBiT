from dasbit.irc.message import Generic

class Numeric(Generic):
    def __init__(self, prefix, command, args):
        Generic.__init__(self, prefix, int(command), args)
