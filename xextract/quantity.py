import re

import six


# quantity types
Q_INVALID = 0
Q_STAR = 1
Q_PLUS = 2
Q_QUES = 3
Q_1D = 4
Q_2D = 5


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
        num1, num2 - number of items in interval [num1, num2] (0 <= num1 <= num2).
    '''

    _quant_re = re.compile(
        r'^\s*(\*|\+|\?|\s*(\d+)\s*|\s*(\d+)\s*,\s*(\d+)\s*)\s*$', re.UNICODE)

    def __init__(self, quantity='*'):
        self.raw_quantity = quantity
        self.quantity_type = self._parse_quantity(quantity)
        if self.quantity_type == Q_INVALID:
            raise ValueError('Invalid quantity: "%s"' % quantity)

    def check_quantity(self, n):
        if not isinstance(n, six.integer_types):
            raise ValueError('Invalid argument for "check_quantity()".'
                'Integer expected, %s received: "%s"' % (type(n), n))
        if self.quantity_type == Q_STAR:
            return n >= 0
        elif self.quantity_type == Q_PLUS:
            return n >= 1
        elif self.quantity_type == Q_QUES:
            return n == 0 or n == 1
        elif self.quantity_type == Q_1D:
            return n == self.num
        elif self.quantity_type == Q_2D:
            return self.num1 <= n and n <= self.num2
        return False

    def _parse_quantity(self, quantity):
        if isinstance(quantity, six.integer_types):
            self.num = quantity
            if 0 <= self.num:
                return Q_1D
            else:
                return Q_INVALID

        if isinstance(quantity, (list, tuple)) and len(quantity) == 2:
            self.num1, self.num2 = quantity
            if (isinstance(self.num1, six.integer_types) and
                    isinstance(self.num2, six.integer_types) and
                    0 <= self.num1 <= self.num2):
                return Q_2D
            else:
                return Q_INVALID

        match = self._quant_re.match(quantity)
        if not match:
            return Q_INVALID

        if match.group(4):
            self.num1 = int(match.group(3))
            self.num2 = int(match.group(4))
            if 0 <= self.num1 <= self.num2:
                return Q_2D
            else:
                return Q_INVALID
        elif match.group(2):
            self.num = int(match.group(2))
            if 0 <= self.num:
                return Q_1D
            else:
                return Q_INVALID
        elif match.group(1) == '*':
            return Q_STAR
        elif match.group(1) == '+':
            return Q_PLUS
        elif match.group(1) == '?':
            return Q_QUES
        return Q_INVALID

    @property
    def is_single(self):
        return (self.quantity_type == Q_QUES or
            (self.quantity_type == Q_1D and self.num <= 1))
