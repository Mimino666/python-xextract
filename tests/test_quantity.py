import unittest

from xextract.quantity import Quantity


class TestQuantity(unittest.TestCase):
    def test_create(self):
        self.assertEqual(Quantity().raw_quantity, '*')
        good = ['   *', ' +    ', '?    ', ' 1321     ', '007',
            ' 8800,    9231   ', '1,2', '9999', '5,5', 9999, '0', '10000', 0, 10000,
            (1, 2), (0, 0)]
        for g in good:
            quantity = Quantity(g)
            self.assertIsNotNone(quantity._check_quantity_func)

        bad = ['', None, ' * * ', '+*', '  ', '1 2', '1,2,3', '+2', '-2', '3,2', 1.0,
                -1, (3, 2), (-1, 5)]
        for b in bad:
            self.assertRaises(ValueError, Quantity, b)

    def test_err(self):
        q = Quantity('*')
        err = ['0', [0], None, 'help']
        for e in err:
            self.assertRaises(ValueError, q.check_quantity, e)

    def test_star(self):
        q = Quantity('*')
        self._test_good(q, [0, 1, 2, 5, 10, 1000, 2**30])
        self._test_bad(q, [-1, -2])

    def test_plus(self):
        q = Quantity('+')
        self._test_good(q, [1, 2, 5, 10, 1000, 2**30])
        self._test_bad(q, [0, -1, -2])

    def test_ques(self):
        q = Quantity('?')
        self._test_good(q, [0, 1])
        self._test_bad(q, [-2, -1, 2, 3, 10, 100])

    def test_1d(self):
        q = Quantity('47')
        self._test_good(q, [47])
        self._test_bad(q, [0, 1, -1, -47, 46, 48, 100])

        q = Quantity(47)
        self._test_good(q, [47])
        self._test_bad(q, [0, 1, -1, -47, 46, 48, 100])

    def test_2d(self):
        q = Quantity('5, 10')
        self._test_good(q, [5, 6, 7, 8, 9, 10])
        self._test_bad(q, [0, 1, 2, 3, 4, 11, 12, 13, -5, -10])

        q = Quantity((5, 10))
        self._test_good(q, [5, 6, 7, 8, 9, 10])
        self._test_bad(q, [0, 1, 2, 3, 4, 11, 12, 13, -5, -10])

    def _test_good(self, q, good):
        for g in good:
            self.assertTrue(q.check_quantity(g))

    def _test_bad(self, q, bad):
        for b in bad:
            self.assertFalse(q.check_quantity(b))
