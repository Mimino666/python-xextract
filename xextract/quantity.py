import re


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
        num - specified number of items (0 <= num <= 9999)
        num1, num2 - number of items in interval [num1, num2] (0 <= num1 <= num2 <= 9999).
    '''

    _quant_re = re.compile(
        r'^\s*(\*|\+|\?|\s*(\d{1,4})\s*|\s*(\d{1,4})\s*,\s*(\d{1,4})\s*)\s*$')

    def __init__(self, quantity='*'):
        self.raw_quantity = quantity
        self.quantity = self._parse_quantity(quantity)
        if self.quantity == Q_INVALID:
            raise ValueError('Invalid quantity syntax: %s' % quantity)

    def check_quantity(self, n):
        if not isinstance(n, int):
            raise ValueError('Invalid argument for `check_quantity()`.'
                'Integer expected, %s received: %s' % (type(n), n))
        if self.quantity == Q_STAR:
            return n >= 0
        elif self.quantity == Q_PLUS:
            return n >= 1
        elif self.quantity == Q_QUES:
            return n == 0 or n == 1
        elif self.quantity == Q_1D:
            return n == self.dig
        elif self.quantity == Q_2D:
            return self.dig1 <= n and n <= self.dig2
        return False

    def _parse_quantity(self, quantity):
        match = self._quant_re.match(quantity)
        if not match:
            return Q_INVALID

        if match.group(4) is not None:
            self.dig1 = int(match.group(3))
            self.dig2 = int(match.group(4))
            if self.dig1 < 0 or self.dig1 > self.dig2:
                return Q_INVALID
            return Q_2D
        elif match.group(2) is not None:
            self.dig = int(match.group(2))
            if self.dig < 0:
                return Q_INVALID
            return Q_1D
        elif match.group(1) == '*':
            return Q_STAR
        elif match.group(1) == '+':
            return Q_PLUS
        elif match.group(1) == '?':
            return Q_QUES
        return Q_INVALID
