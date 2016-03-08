import re

import six


class Quantity(object):
    '''Quantity provides a conveniet way to verify the number of objects.
    With a regexp-like syntax specify, what number of objects do you expect.
    By calling `check_quantity()` method you can verify whether the number
    of objects satisfies the specified value.

    Syntax:
        * - zero or more items
        + - one or more items
        ? - zero or one item
        num - specified number of items (0 <= num)
        lower, upper - number of items in interval [lower, upper] (0 <= lower <= upper).
    '''
    def __init__(self, quantity='*'):
        self.raw_quantity = quantity
        self.lower = self.upper = 0
        self._check_quantity = self._parse_quantity(quantity)
        if self._check_quantity is None:
            raise ValueError('Invalid quantity: "%s"' % repr(quantity))

    def check_quantity(self, n):
        if not isinstance(n, six.integer_types):
            raise ValueError('Invalid argument for "check_quantity()".'
                'Integer expected, %s received: "%s"' % (type(n), n))
        return self._check_quantity(n)

    def _check_star(self, n):
        return n >= 0

    def _check_plus(self, n):
        return n >= 1

    def _check_question_mark(self, n):
        return 0 <= n <= 1

    def _check_1d(self, n):
        return n == self.upper

    def _check_2d(self, n):
        return self.lower <= n <= self.upper

    _quantity_parsers = (
        # regex, check_funcname
        (re.compile(r'^\s*\*\s*$'), '_check_star'),
        (re.compile(r'^\s*\+\s*$'), '_check_plus'),
        (re.compile(r'^\s*\?\s*$'), '_check_question_mark'),
        (re.compile(r'^\s*(?P<upper>\d+)\s*$'), '_check_1d'),
        (re.compile(r'^\s*(?P<lower>\d+)\s*,\s*(?P<upper>\d+)\s*$'), '_check_2d'))

    def _parse_quantity(self, quantity):
        # quantity is specified as single integer
        if isinstance(quantity, six.integer_types):
            self.upper = quantity
            if 0 <= self.upper:
                return self._check_1d
            else:
                return None

        # quantity is specified as pair of integers
        if isinstance(quantity, (list, tuple)) and len(quantity) == 2:
            self.lower, self.upper = quantity
            if (isinstance(self.lower, six.integer_types) and
                    isinstance(self.upper, six.integer_types) and
                    0 <= self.lower <= self.upper):
                return self._check_2d
            else:
                return None

        if not isinstance(quantity, six.string_types):
            return None

        # parse quantity
        for parser, check_funcname in self._quantity_parsers:
            match = parser.search(quantity)
            if match:
                # parse groupdict values
                for k, v in match.groupdict().iteritems():
                    setattr(self, k, int(v))
                # final check of lower/upper bounds
                if self.lower <= self.upper:
                    return getattr(self, check_funcname)
                else:
                    return None
        return None

    @property
    def is_single(self):
        '''True, if the quantity represents a single element.'''
        return (self._check_quantity == self._check_question_mark or
            (self._check_quantity == self._check_1d and self.upper <= 1))
