import os
import re
from twisted.internet import defer
from dasbit.core import Config

class User:
    help = 'https://github.com/DASPRiD/DASBiT/wiki/User-Plugin'

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
        manager.registerCommand('user', 'acl', 'acl-set', '(?P<username>[^ ]+) (?P<aclString>.+)', self.setAcl)
        manager.registerCommand('user', 'acl', 'acl-add', '(?P<username>[^ ]+) (?P<aclString>.+)', self.addAcl)
        manager.registerCommand('user', 'acl', 'acl-remove', '(?P<username>[^ ]+) (?P<aclString>.+)', self.removeAcl)
        manager.registerCommand('user', 'acl', 'acl-show', '(?P<username>[^ ]+)', self.showAcl)
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

    def setAcl(self, source, username, aclString):
        self._storeAcl(source, username, aclString, 'set')

    def addAcl(self, source, username, aclString):
        self._storeAcl(source, username, aclString, 'add')

    def removeAcl(self, source, username, aclString):
        self._storeAcl(source, username, aclString, 'remove')

    def _storeAcl(self, source, username, aclString, mode):
        if username in self.acl:
            self.acl[username].modify(aclString, mode)
        elif mode != 'remove':
            self.acl[username] = Acl(aclString)

        self.config[username] = repr(self.acl[username])
        self.config.save()

        self.client.reply(source, 'ACL has been modified', 'notice')

    def showAcl(self, source, username):
        if username in self.acl:
            self.client.reply(source, 'ACL for %s: %s' % (username, repr(self.acl[username])), 'notice')
        else:
            self.client.reply(source, 'No ACL for %s found' % username, 'notice')

    def verifyAccess(self, source, permission):
        if '*' in self.acl and self.acl['*'].isAllowed(permission):
            return True

        rd = defer.Deferred()

        d = defer.maybeDeferred(self._determineUsername, source.prefix)
        d.addCallback(self._checkAcl, rd, permission)

        return rd

    def _checkAcl(self, username, rd, permission):
        if not username in self.acl:
            rd.callback(False)
        else:
            rd.callback(self.acl[username].isAllowed(permission))

    def _determineUsername(self, prefix):
        if prefix['ident'] in self.identToUsername:
            return self.identToUsername[prefix['ident']]

        if not prefix['nickname'] in self.nicknameDefers:
            self.nicknameToIdent[prefix['nickname']] = prefix['ident']
            self.client.send('WHOIS', prefix['nickname'])

            self.nicknameDefers[prefix['nickname']] = defer.Deferred()

        return self.nicknameDefers[prefix['nickname']]

    def whoisReceived(self, message):
        if message.command == 330:
            nickname = message.args[1]
            username = message.args[2]

            self.identToUsername[self.nicknameToIdent[nickname]] = username

            if nickname in self.nicknameDefers:
                self.nicknameDefers[nickname].callback(username)
                del self.nicknameDefers[nickname]
        elif message.command == 318:
            nickname = message.args[1]

            if nickname in self.nicknameDefers:
                self.client.sendNotice(nickname, 'You are not identified with NickServ')

                del self.nicknameDefers[nickname]

class Acl:
    def __init__(self, aclString = None):
        self.resources = {}

        if aclString is not None:
            self.modify(aclString, 'set')

    def modify(self, aclString, mode):
        if mode == 'set':
            self.resources = {}
            mode = 'add'

        if not aclString.strip():
            return

        permissions = re.split('[ ]+', aclString.strip())

        if mode == 'add':
            for permission in permissions:
                if '.' in permission:
                    resource, privilege = permission.split('.', 1)
                else:
                    resource  = permission
                    privilege = '*'

                if not resource in self.resources:
                    self.resources[resource] = {}

                self.resources[resource][privilege] = True
        elif mode == 'remove':
            for permission in permissions:
                if '.' in permission:
                    resource, privilege = permission.split('.', 1)
                else:
                    resource  = permission
                    privilege = '*'

                if not resource in self.resources:
                    continue

                if privilege in self.resources[resource]:
                    del self.resources[resource][privilege]

    def isAllowed(self, permission):
        resource, privilege = permission.split('.', 1)

        if '*' in self.resources and \
            ('*' in self.resources['*'] or \
            privilege in self.resources['*']):
            return True

        if resource in self.resources and \
            ('*' in self.resources[resource] or \
            privilege in self.resources[resource]):
            return True

        return False

    def __repr__(self):
        permissions = []

        for resource, privileges in self.resources.iteritems():
            for privilege, mode in privileges.iteritems():
                permissions.append(('' if mode else '-') + resource + '.' + privilege)

        return ' '.join(permissions)


