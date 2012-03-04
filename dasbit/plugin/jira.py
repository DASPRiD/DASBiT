import os
import time
from calendar import timegm
from urllib import urlencode
from xml.etree.ElementTree import XML
from dasbit.core import Config
from twisted.web.client import getPage
from twisted.internet import defer

class Jira:
    def __init__(self, manager):
        self.client = manager.client
        self.config = Config(os.path.join(manager.dataPath, 'jira'))

        if not 'instances' in self.config:
            self.config['instances'] = []

        manager.registerCommand('jira', 'add', 'jira-add', '(?P<channel>[^ ]+) (?P<url>[^ ]+) (?P<project>[^ ]+)', self.add)
        manager.registerCommand('jira', 'remove', 'jira-remove', '(?P<channel>[^ ]+) (?P<project>[^ ]+)', self.remove)
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
        pd.addCallback(self._parseIssueUpdates, rd, timeStruct)
        pd.addErrback(rd.errback)

        return rd

    def _parseIssueUpdates(self, value, rd, lastIssueTime):
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
