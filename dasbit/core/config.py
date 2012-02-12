import json
import os

class Config(dict):
    def __init__(self, filename):
        self.filename = filename

        if os.path.exists(filename):
            try:
                fp = open(filename, 'r')
                data = json.load(fp, object_hook = self._decodeDict)
                fp.close()

                for key, value in data.iteritems():
                    dict.__setitem__(self, key, value)
            except:
                pass

    def save(self):
        fp = open(self.filename, 'w')
        json.dump(dict.copy(self), fp)
        fp.close()

    def _decodeList(self, data):
        result = []

        for item in data:
            if isinstance(item, unicode):
                item = item.encode('utf-8')
            elif isinstance(item, list):
                item = self._decodeList(item)
            elif isinstance(item, dict):
                item = self._decodeDict(item)

            result.append(item)

        return result

    def _decodeDict(self, data):
        result = {}

        for key, value in data.iteritems():
            if isinstance(key, unicode):
                key = key.encode('utf-8')

            if isinstance(value, unicode):
                value = value.encode('utf-8')
            elif isinstance(value, list):
                value = self._decodeList(value)
            elif isinstance(value, dict):
                value = self._decodeDict(value)

            result[key] = value

        return result
