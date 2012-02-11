import re

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
                elif len(part == 1):
                    tag  = part[0]
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
"""

    /**
     * Unpack a message.
     *
     * The returned array will contain all splitted standard and extended
     * messages. Standard messages will simply be strings, while extended
     * messages will be represented as arrays containing 'tag' and 'data'.
     *
     * @param  string $message
     * @return array
     */
    public function unpackMessage($message)
    {
        $message = $this->lowLevelDequote($message);

        preg_match_all(
            "("
            . "(" . self::DELIMITER . ")?"
            . "(?(1)"
            .   "[^" . self::DELIMITER . "]*" . self::DELIMITER
            . "|"
            .   ".+?(?:$|(?=" . self::DELIMITER ."))"
            . "))Ss",
            $message,
            $matches
        );

        $parts           = array();
        $standardMessage = '';

        foreach ($matches[0] as $match) {
            $match = $this->ctcpDequote($match);

            if ($match[0] === self::DELIMITER) {
                $extendedMessage = $this->parseExtendedMessage($match);

                if ($extendedMessage !== null) {
                    $parts[] = $extendedMessage;
                }
            } else {
                $standardMessage .= $match;
            }
        }

        if (!empty($standardMessage)) {
            $parts[] = $standardMessage;
        }

        return $parts;
    }

    /**
     * Parse an extended message.
     *
     * @param  string $message
     * @return array
     */
    protected function parseExtendedMessage($message)
    {
        $result = preg_match(
            "(" . self::DELIMITER
            . "(?:(?<tag>[^\1\40]+)(?: (?<data>[^\1]*))?)?"
            . self::DELIMITER . ")",
            $message,
            $matches
        );

        if ($result === 1 && isset($matches['tag'])) {
            if (!in_array($matches['tag'], $this->allowedTags)) {
                return null;
            }

            $result = array(
                'tag' => $matches['tag']
            );

            if (isset($matches['data'])) {
                $result['data'] = $matches['data'];
            } else {
                $result['data'] = null;
            }

            return $result;
        }

        return null;
    }
"""
