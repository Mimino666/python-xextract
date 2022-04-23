import re


class Quantity(object):
    '''
    Quantity is used to verify that the number of items satisfies the
    expected quantity, which you specify with a regexp-like syntax.

    Syntax:
        * - zero or more items
        + - one or more items
        ? - zero or one item
        count - specified number of items (0 <= count)
        lower, upper - number of items in interval [lower, upper] (0 <= lower <= upper).
    '''

    def __init__(self, quantity='*'):
        self.raw_quantity = quantity
        self.lower = self.upper = 0  # lower and upper bounds on quantity
        self._check_quantity_func = self._parse_quantity(quantity)

    def check_quantity(self, n):
        '''Return True, if `n` matches the specified quantity.'''

        if not isinstance(n, int):
            raise ValueError(
                'Invalid argument for "check_quantity()". '
                'Integer expected, %s received: "%s"' % (type(n), n))
        return self._check_quantity_func(n)

    def _check_star(self, n):
        return n >= 0

    def _check_plus(self, n):
        return n >= 1

    def _check_question_mark(self, n):
        return n == 0 or n == 1

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
        '''
        If `quantity` represents a valid quantity expression, return the
        method that checks for the specified quantity.

        Otherwise raise ValueError.
        '''

        # quantity is specified as a single integer
        if isinstance(quantity, int):
            self.upper = quantity
            if 0 <= self.upper:
                return self._check_1d
            else:
                raise ValueError('Invalid quantity: "%s"' % repr(quantity))

        # quantity is specified as a pair of integers
        if isinstance(quantity, (list, tuple)) and len(quantity) == 2:
            self.lower, self.upper = quantity
            if (isinstance(self.lower, int) and
                    isinstance(self.upper, int) and
                    0 <= self.lower <= self.upper):
                return self._check_2d
            else:
                raise ValueError('Invalid quantity: "%s"' % repr(quantity))

        # quantity is specified as a string
        if isinstance(quantity, str):
            for parser, check_funcname in self._quantity_parsers:
                match = parser.search(quantity)
                if match:
                    # set lower and upper values
                    gd = match.groupdict()
                    self.lower = int(gd.get('lower', 0))
                    self.upper = int(gd.get('upper', 0))
                    # check lower/upper bounds
                    if self.lower <= self.upper:
                        return getattr(self, check_funcname)
                    else:
                        raise ValueError('Invalid quantity: "%s"' % repr(quantity))

        # quantity is of a bad type
        raise ValueError('Invalid quantity: "%s"' % repr(quantity))

    @property
    def is_single(self):
        '''True, if the quantity represents a single element.'''

        return (
            self._check_quantity_func == self._check_question_mark or
            (self._check_quantity_func == self._check_1d and self.upper <= 1))
