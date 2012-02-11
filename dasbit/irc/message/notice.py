from dasbit.irc.message import Generic

class Notice(Generic):
    def __init__(self, prefix, command, args):
        Generic.__init__(self, prefix, command, args)

        self.target  = args[0]
        self.message = args[1]