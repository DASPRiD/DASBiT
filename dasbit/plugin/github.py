import os
import time
import json
from calendar import timegm
from urllib import urlencode, quote_plus
from dasbit.core import Config
from twisted.web.client import getPage
from twisted.internet import defer

class Github:
    def __init__(self, manager):
        self.client       = manager.client
        self.config       = Config(os.path.join(manager.dataPath, 'github'))

        if not 'instances' in self.config:
            self.config['instances'] = []

        manager.registerCommand('github', 'add', 'github-add', '(?P<channel>[^ ]+) (?P<owner>[^ ]+) (?P<repository>[^ ]+)', self.add)
        manager.registerCommand('github', 'remove', 'github-remove', '(?P<channel>[^ ]+) (?P<owner>[^ ]+) (?P<repository>[^ ]+)', self.remove)
        manager.registerInterval('github', 60, self.watchForUpdates)

    def add(self, source, channel, owner, repository):
        for instance in self.config['instances']:
            if instance['channel'] == channel and instance['owner'] == owner and instance['repository'] == repository:
                self.client.reply(source, 'This project is already watched', 'notice')
                return

        d = self._getIssueUpdates(owner, repository, time.time())
        d.addCallback(self._addSuccess, source, channel, owner, repository)
        d.addErrback(self._addError, source)

    def _addSuccess(self, data, source, channel, owner, repository):
        self.config['instances'].append({
            'channel':         channel,
            'owner':           owner,
            'repository':      repository,
            'last-issue-time': time.time()
        })
        self.config.save()

        self.client.reply(source, 'Project added for watching', 'notice')

    def _addError(self, failure, source):
        print failure
        self.client.reply(source, 'Could not reach Github instance', 'notice')

    def remove(self, source, channel, owner, repository):
        for index, instance in enumerate(self.config['instances']):
            if instance['channel'] == channel and instance['project'] == project and instance['repository'] == repository:
                del self.config['instances'][index]
                self.config.save()

                self.client.reply(source, 'Project removed from watching', 'notice')
                return

        self.client.reply(source, 'Could not find project', 'notice')

    def watchForUpdates(self):
        for instance in self.config['instances']:
            d = self._getIssueUpdates(instance['owner'], instance['repository'], instance['last-issue-time'])
            d.addCallback(self._updatesReceived, instance)

    def _updatesReceived(self, issues, instance):
        lastIssueTime = time.gmtime(instance['last-issue-time'])
        newIssueTime  = time.gmtime(instance['last-issue-time'])

        for issue in issues:
            if issue['updated'] <= lastIssueTime:
                continue

            if issue['updated'] > newIssueTime:
                newIssueTime = issue['updated']

            if not issue['labels']:
                labels = 'none'
            else:
                labels = ','.join(issue['labels'])

            self.client.sendPrivMsg(
                instance['channel'],
                '[Issue-Update:%s] [Labels:%s] %s, see: %s' % (
                    issue['id'],
                    labels,
                    issue['summary'],
                    issue['link']
                )
            )

        instance['last-issue-time'] = timegm(newIssueTime)
        self.config.save()

    def _getIssueUpdates(self, owner, repository, lastIssueTime):
        timeStruct = time.gmtime(lastIssueTime)

        url = "https://api.github.com/repos/%s/%s/issues?sort=updated&since=%s" % (
            owner,
            repository,
            time.strftime('%Y-%m-%dT%H:%M:%SZ', timeStruct)
        )

        rd = defer.Deferred()
        pd = getPage(url)
        pd.addCallback(self._parseIssueFeed, rd)
        pd.addErrback(rd.errback)

        return rd

    def _parseIssueFeed(self, value, rd):
        try:
            issues = json.loads(value)
        except:
            rd.errback()
            return

        data = []

        for issue in issues:
            timeStruct = time.strptime(issue['updated_at'], '%Y-%m-%dT%H:%M:%SZ')

            labels = []

            if 'labels' in issue:
                for label in issue['labels']:
                    labels.append(label['name'])

            data.append({
                'id':      issue['id'],
                'link':    issue['html_url'],
                'summary': issue['title'],
                'labels':  labels,
                'updated': timeStruct,
            })

        rd.callback(data)

