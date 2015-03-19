import unittest
from copernicus import BitPattern

__author__ = 'gronostaj'


class BitPatternTests(unittest.TestCase):

    pattern = BitPattern('0101____')

    def test_should_match_low_bound(self):
        self.assertTrue(BitPatternTests.pattern.matches('01010000'))

    def test_should_match_high_bound(self):
        self.assertTrue(BitPatternTests.pattern.matches('01011111'))

    def test_should_match_middle(self):
        self.assertTrue(BitPatternTests.pattern.matches('01010011'))

    def test_should_not_match_below_low_bound(self):
        self.assertFalse(BitPatternTests.pattern.matches('01001111'))

    def test_should_not_match_above_high_bound(self):
        self.assertFalse(BitPatternTests.pattern.matches('01100000'))
