class Vote:
    def __init__(self, manager):
        self.client = manager.client
        self.votes  = {}

        manager.registerCommand('vote', 'control-vote', 'start-vote', '(?P<topic>.*?)', self.startVote)
        manager.registerCommand('vote', 'control-vote', 'end-vote', None, self.endVote)
        manager.registerMessage('vote', self.vote)

    def startVote(self, source, topic):
        channel = source.target.lower()

        if channel in self.votes:
            self.client.reply(source, 'There is already a vote running', 'notice')
            return

        self.votes[channel] = {
            'topic':     topic,
            'positives': 0,
            'negatives': 0,
            'neutrals':  0,
            'users':     []
        }

        self.client.reply(source, 'Vote "%s"; type either +1, -1 or 0' % topic)

    def endVote(self, source):
        channel = source.target.lower()

        if not channel in self.votes:
            self.client.reply(source, 'There is no vote running', 'notice')
            return

        self.client.reply(
            source,
            'Vote result for "%s": %s positives, %s negatives and %s neutrals, consensus: %s' % (
                self.votes[channel]['topic'],
                self.votes[channel]['positives'],
                self.votes[channel]['negatives'],
                self.votes[channel]['neutrals'],
                self.votes[channel]['positives'] - self.votes[channel]['negatives']
            )
        )

        del self.votes[channel]

    def vote(self, message):
        channel = message.target.lower()
        choice  = message.message.strip()

        if not channel in self.votes or choice not in ['+1', '-1', '0']:
            return
        elif message.prefix['ident'] in self.votes[channel]['users']:
            self.client.reply(message, 'You have already voted', 'notice')
        elif choice == '+1':
            self.votes[channel]['positives'] += 1
        elif choice == '-1':
            self.votes[channel]['negatives'] += 1
        elif choice == '0':
            self.votes[channel]['neutrals'] += 1

        self.votes[channel]['users'].append(message.prefix['ident'])
        self.client.reply(message, 'Your vote has been recorded', 'notice')
        
