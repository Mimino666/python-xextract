import unittest

from xextract.utils.python import flatten


class TestPython(unittest.TestCase):
    def test_flatten(self):
        self.assertListEqual(
            flatten([1, 2, [3, 4], (5, 6)]),
            [1, 2, 3, 4, 5, 6])
        self.assertListEqual(
            flatten([[[1, 2, 3], (42, None)], [4, 5], [6], 7, (8, 9, 10)]),
            [1, 2, 3, 42, None, 4, 5, 6, 7, 8, 9, 10])
        self.assertListEqual(
            flatten(xrange(3)),
            [0, 1, 2])
