from __future__ import unicode_literals


class RQLFilterError(Exception):
    MESSAGE = 'RQL Filtering error.'

    def __init__(self, details=None):
        super(RQLFilterError, self).__init__(self.MESSAGE)
        self.details = details


class RQLFilterParsingError(RQLFilterError):
    MESSAGE = 'RQL Parsing error.'


class RQLFilterLookupError(RQLFilterError):
    MESSAGE = 'RQL Lookup error.'


class RQLFilterValueError(RQLFilterError):
    MESSAGE = 'RQL Value error.'
