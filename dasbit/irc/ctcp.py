class Ctcp:
    def __init__(self):
        self.delimiter = '\1'
        self.mQuote    = '\20'
        self.xQuote    = '\134'

        self.mQuoteMap = {
            self.mQuote: self.mQuote,
            '\0':        '0',
            '\r':        'r',
            '\n':        'n'
        }

        self.xQuoteMap = {
            self.xQuote:    self.xQuote,
            self.delimiter: 'a'
        }

        self.allowedTags = [
            'VERSION', 'PING', 'CLIENTINFO', 'ACTION', 'FINGER', 'TIME', 'DCC',
            'ERRMSG', 'PLAY'
        ]

    def packMessage(self, parts):
        extendedMessage = ''
        standardMessage = ''

        for part in parts:
            if isinstance(part, tuple):
                if len(part) == 0:
                    tag  = None
                    data = None
                elif len(part) == 1:
                    tag  = part[0].upper()
                    data = None
                else:
                    (tag, data) = part

                extendedMessage += self.createExtendedMessage(tag, data)
            else:
                standardMessage += self.ctcpQuote(part)

        return self.lowLevelQuote(extendedMessage + standardMessage)

    def createExtendedMessage(self, tag, data):
        message = self.delimiter

        if tag is not None:
            if not tag in self.allowedTags:
                raise Exception('%s is not a valid tag' % tag)

            message += self.ctcpQuote(tag)

            if data is not None:
                message += ' ' + self.ctcpQuote(data)

        message += self.delimiter

        return message

    def unpackMessage(self, message):
        message         = self.lowLevelDequote(message)
        parts           = []
        part            = ''
        length          = len(message)
        currentPos      = 0
        isExtended      = None
        standardMessage = ''

        while currentPos < length:
            if isExtended is None:
                if message[currentPos] == self.delimiter:
                    isExtended = True
                    part = ''
                else:
                    isExtended = False
                    part = message[currentPos]
            else:
                if message[currentPos] == self.delimiter:
                    if isExtended:
                        extendedMessage = self.parseExtendedMessage(part)

                        if extendedMessage is not None:
                            parts.append(extendedMessage)

                        isExtended = False
                    else:
                        standardMessage += part
                        isExtended = True
                        part       = ''
                else:
                    part += message[currentPos]

            currentPos += 1

        if part:
            standardMessage += part

        if standardMessage:
            parts.append(standardMessage)

        return parts

    def parseExtendedMessage(self, message):
        if not message:
            return None

        if ' ' in message:
            tag, data = message.split(' ', 1)
        else:
            tag  = message
            data = None

        return (tag, data)

    def ctcpQuote(self, string):
        return self.quote(self.xQuoteMap, self.xQuote, self.xQuote + self.delimiter, string)

    def ctcpDequote(self, string):
        return self.dequote(self.xQuoteMap, self.xQuote, string)

    def lowLevelQuote(self, string):
        return self.quote(self.mQuoteMap, self.mQuote, self.mQuote + '\0\n\r', string)

    def lowLevelDequote(self, string):
        return self.dequote(self.mQuoteMap, self.mQuote, string)

    def quote(self, quoteMap, quoteChar, specialChars, string):
        for specialChar in specialChars:
            string = string.replace(specialChar, quoteChar + quoteMap[specialChar])

        return string

    def dequote(self, quoteMap, quoteChar, string):
        result     = ''
        length     = len(string)
        currentPos = 0

        while currentPos < length:
            if string[currentPos] == quoteChar:
                currentPos += 1

                if currentPos < length:
                    if string[currentPos] in quoteMap:
                        result += quoteMap[string[currentPos]]
                    else:
                        result += string[currentPos]

                    currentPos += 1
            else:
                result     += string[currentPos]
                currentPos += 1

        return result
