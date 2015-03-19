import unittest
from copernicus import Command

__author__ = 'gronostaj'


class CommandTests(unittest.TestCase):

    def test_should_insert_value_correctly(self):
        cmd = Command('0011____')
        inserted = cmd.translate(10)
        self.assertEqual(inserted, chr(58))

    def test_should_insert_all_wildcards_mask_value_correctly(self):
        cmd = Command('________')
        inserted = cmd.translate(42)
        self.assertEqual(inserted, chr(42))

    def test_should_reject_too_long_value(self):
        cmd = Command('000000__')
        with self.assertRaises(ValueError):
            cmd.translate(4)

    def test_should_do_transforms_correctly(self):
        cmd = Command('000000__', lambda x, y: x + y)
        inserted = cmd.translate(1, 2)
        self.assertEqual(inserted, chr(3))