import os
import time
import re
from calendar import timegm
from urllib import urlencode, quote_plus
from xml.etree.ElementTree import XML
from dasbit.core import Config
from twisted.web.client import getPage
from twisted.internet import defer

class Jira:
    def __init__(self, manager):
        self.client       = manager.client
        self.config       = Config(os.path.join(manager.dataPath, 'jira'))
        self.triggerRegex = re.compile('@(?P<key>[A-Za-z][A-Za-z0-9]*)-(?P<id>[1-9]\d*)')

        if not 'instances' in self.config:
            self.config['instances'] = []

        manager.registerCommand('jira', 'add', 'jira-add', '(?P<channel>[^ ]+) (?P<url>[^ ]+) (?P<project>[^ ]+)', self.add)
        manager.registerCommand('jira', 'remove', 'jira-remove', '(?P<channel>[^ ]+) (?P<project>[^ ]+)', self.remove)
        manager.registerMessage('jira', self.lookup)
        manager.registerInterval('jira', 60, self.watchForUpdates)

    def add(self, source, channel, url, project):
        for instance in self.config['instances']:
            if instance['channel'] == channel and instance['project'] == project:
                self.client.reply(source, 'This project is already watched', 'notice')
                return

        d = self._getIssueUpdates(url, project, time.time())
        d.addCallback(self._addSuccess, source, channel, url, project)
        d.addErrback(self._addError, source)

    def _addSuccess(self, data, source, channel, url, project):
        self.config['instances'].append({
            'channel':         channel,
            'url':             url,
            'project':         project,
            'last-issue-time': time.time()
        })
        self.config.save()

        self.client.reply(source, 'Project added for watching', 'notice')

    def _addError(self, failure, source):
        self.client.reply(source, 'Could not reach Jira instance', 'notice')

    def remove(self, source, channel, project):
        for index, instance in enumerate(self.config['instances']):
            if instance['channel'] == channel and instance['project'] == project:
                del self.config['instances'][index]
                self.config.save()

                self.client.reply(source, 'Project removed from watching', 'notice')
                return

        self.client.reply(source, 'Could not find project', 'notice')

    def lookup(self, message):
        matches = self.triggerRegex.finditer(message.message)
        
        if matches is None:
            return

        for match in matches:
            result = match.groupdict()
            found  = False

            for index, instance in enumerate(self.config['instances']):
                if instance['project'].lower() == result['key'].lower():
                    d = self._fetchIssue(message, instance, result['id'])
                    d.addCallback(self._reportIssue, message)
                    d.addErrback(self._reportIssueFailure, message, result['key'] + '-' + result['id'])
                    found = True
                    break

            if not found:
                self.client.reply(message, 'Could not find issue %s' % (result['key'] + '-' + result['id']), 'notice')

    def watchForUpdates(self):
        for instance in self.config['instances']:
            d = self._getIssueUpdates(instance['url'], instance['project'], instance['last-issue-time'])
            d.addCallback(self._updatesReceived, instance)

    def _updatesReceived(self, issues, instance):
        lastIssueTime = time.gmtime(instance['last-issue-time'])
        newIssueTime  = time.gmtime(instance['last-issue-time'])

        for issue in issues:
            if issue['updated'] <= lastIssueTime:
                continue

            if issue['updated'] > newIssueTime:
                newIssueTime = issue['updated']

            self.client.sendPrivMsg(
                instance['channel'],
                '[Issue-Update:%s] [Type:%s] [Status:%s] [Component:%s] %s, see: %s' % (
                    issue['key'],
                    issue['type'],
                    issue['status'],
                    issue['component'],
                    issue['summary'],
                    issue['link']
                )
            )

        instance['last-issue-time'] = timegm(newIssueTime)
        self.config.save()

    def _getIssueUpdates(self, baseUrl, project, lastIssueTime):
        timeStruct = time.gmtime(lastIssueTime)

        jqlQuery = "project = %s AND updated >= '%s' ORDER BY updated ASC, key DESC" % (
            project,
            time.strftime('%Y-%m-%d %H:%M', timeStruct)
        )

        url = '%s/sr/jira.issueviews:searchrequest-xml/temp/SearchRequest.xml?%s' % (
            baseUrl,
            urlencode([
                ('jqlQuery', jqlQuery),
                ('field', 'key'),
                ('field', 'link'),
                ('field', 'summary'),
                ('field', 'type'),
                ('field', 'status'),
                ('field', 'component'),
                ('field', 'updated')
            ])
        )

        rd = defer.Deferred()
        pd = getPage(url)
        pd.addCallback(self._parseIssueFeed, rd)
        pd.addErrback(rd.errback)

        return rd

    def _reportIssueFailure(self, failure, message, issueKey):
        print failure
        self.client.reply(message, 'Could not find issue %s' % issueKey, 'notice')

    def _reportIssue(self, issues, message):
        issue = issues[0]

        self.client.reply(
            message,
            '[Issue:%s] [Type:%s] [Status:%s] [Component:%s] %s, see: %s' % (
                issue['key'],
                issue['type'],
                issue['status'],
                issue['component'],
                issue['summary'],
                issue['link']
            )
        )

    def _fetchIssue(self, message, instance, id):
        issueKey = instance['project'] + '-' + id

        url = '%s/si/jira.issueviews:issue-xml/%s/%s.xml' % (
            instance['url'],
            quote_plus(issueKey),
            quote_plus(issueKey)
        )

        rd = defer.Deferred()
        pd = getPage(url)
        pd.addCallback(self._parseIssueFeed, rd)
        pd.addErrback(rd.errback)  

        return rd

    def _parseIssueFeed(self, value, rd):
        try:
            feed = XML(value)
        except:
            rd.errback()
            return

        data = []

        for item in feed.findall('channel/item'):
            timeStruct = time.strptime(item.find('updated').text, '%a, %d %b %Y %H:%M:%S +0000')
            component  = item.find('component')

            if component is None:
                component = 'n/a'
            else:
                component = component.text

            data.append({
                'key':       item.find('key').text,
                'link':      item.find('link').text,
                'summary':   item.find('summary').text,
                'type':      item.find('type').text,
                'status':    item.find('status').text,
                'component': component,
                'updated':   timeStruct,
            })

        rd.callback(data)
