import os
import re
from twisted.internet import defer
from dasbit.core import Config

class User:
    def __init__(self, manager):
        self.manager = manager
        self.client  = manager.client
        self.config  = Config(os.path.join(self.manager.dataPath, 'acl'))
        self.acl     = {}

        for username, aclString in self.config.iteritems():
            self.acl[username] = Acl(aclString)

        self.identToUsername = {}
        self.nicknameToIdent = {}
        self.nicknameDefers  = {}

        manager.registerCommand('user', None, 'master', None, self.setMaster)
        #manager.registerCommand('user', 'acl', 'acl', '(?P<username>[^ ]+) (?P<acl>.+)', self.setAcl)
        manager.registerNumeric('user', [318, 330], self.whoisReceived)

    def setMaster(self, source):
        if len(self.acl) > 0:
            self.client.reply(source, 'Master has already been set', 'notice')
            return

        d = defer.maybeDeferred(self._determineUsername, source.prefix)
        d.addCallback(self._storeMaster, source)

    def _storeMaster(self, username, source):
        self.acl[username]    = Acl('*.*')
        self.config[username] = repr(self.acl[username])
        self.config.save()

        self.client.reply(source, 'You are now the master', 'notice')

    def _determineUsername(self, prefix):
        if self.identToUsername.has_key(prefix['ident']):
            return self.identToUsername[prefix['ident']]

        if not self.nicknameDefers.has_key(prefix['nickname']):
            self.nicknameToIdent[prefix['nickname']] = prefix['ident']
            self.client.send('WHOIS', prefix['nickname'])

            self.nicknameDefers[prefix['nickname']] = defer.Deferred()

        return self.nicknameDefers[prefix['nickname']]

    def whoisReceived(self, message):
        if message.command == 330:
            nickname = message.args[1]
            username = message.args[2]

            self.identToUsername[self.nicknameToIdent[nickname]] = username

            if self.nicknameDefers.has_key(nickname):
                self.nicknameDefers[nickname].callback(username)
                del self.nicknameDefers[nickname]
        elif message.command == 318:
            nickname = message.args[1]

            if self.nicknameDefers.has_key(nickname):
                self.client.sendNotice(nickname, 'You are not identified with NickServ')

                del self.nicknameDefers[nickname]

class Acl:
    def __init__(self, aclString = None):
        self.resources = {}

        if aclString is not None:
            self.modify(aclString)

    def modify(self, aclString):
        mods = re.split('[ ]+', aclString.strip())

        for mod in mods:
            mode = 'allow'

            if (mod.startswith('-')):
                mode = 'deny'
                mod  = mod[1:]
            elif (mod.startswith('+')):
                mod  = mod[1:]

            if '.' in mod:
                resource, privilege = mod.split('.', 1)
            else:
                resource  = mod
                privilege = '*'

            if not self.resources.has_key(resource):
                self.resources[resource] = {}

            self.resources[resource][privilege] = (mode == 'allow')

        if not self.resources.has_key('*') or self.resources['*'].has_key('*'):
            for resource, privileges in self.resources.iteritems():
                if not privileges.has_key('*'):
                    for privilege, mode in privileges.iteritems():
                        if not mode:
                            del self.resources[resource][privilege]
        else:
            for resource, privileges in self.resources.iteritems():
                for privilege, mode in privileges.iteritems():
                    if resource == '*' and privilege == '*':
                        continue
                    elif mode:
                        del self.resources[resource][privilege]

                if len(privileges) == 0:
                    del self.resources[resource]

    def isAllowed(self, restrict):
        resource, privilege = mod.split('.', 1)

        allowed = False

        if self.resources.has_key('*'):
            if self.resources['*'].has_key('*'):
                allowed = True

            if self.resources['*'].has_key(privilege):
                allowed = self.resources['*'][privilege]

        if self.resources.has_key(resource):
            if self.resources[resource].has_key('*'):
                allowed = True

            if self.resources[resource].has_key(privilege):
                allowed = self.resources[resource][privilege]

        return allowed

    def __repr__(self):
        mods = []

        for resource, privileges in self.resources.iteritems():
            for privilege, mode in privileges.iteritems():
                mods.append(('' if mode else '-') + resource + '.' + privilege)

        return ' '.join(mods)


