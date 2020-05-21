#
#  Copyright © 2020 Ingram Micro Inc. All rights reserved.
#


class RQLFilterError(Exception):
    """ Base class for RQL errors. """
    MESSAGE = 'RQL Filtering error.'

    def __init__(self, details=None):
        super(RQLFilterError, self).__init__(self.MESSAGE)
        self.details = details


class RQLFilterParsingError(RQLFilterError):
    """ Parsing errors are raised only at query parsing time. """
    MESSAGE = 'RQL Parsing error.'


class RQLFilterLookupError(RQLFilterError):
    """ Lookup error is raised when provided lookup is not supported by the associated filter. """
    MESSAGE = 'RQL Lookup error.'


class RQLFilterValueError(RQLFilterError):
    """ Value error is raised when provided values can't be converted to DB field types. """
    MESSAGE = 'RQL Value error.'
