import unittest
from copernicus import Event

__author__ = 'gronostaj'


class EventTests(unittest.TestCase):

    event = Event('test', '0101____')

    def test_should_extract_argument_correctly(self):
        min_ = EventTests.event.extract_arg('01010000')
        max_ = EventTests.event.extract_arg('01011111')
        self.assertEqual(min_, 0)
        self.assertEqual(max_, 15)

    def test_should_translate_argument_correctly(self):
        event = Event('test', '0101____', lambda v: 2 * v + 5)
        for x in (0, 2, 10):
            self.assertEqual(event.transform(x), x * 2 + 5)

    def test_should_error_when_extracting_with_non_matching_mask(self):
        with self.assertRaises(ValueError):
            EventTests.event.extract_arg('11111111')

    def test_should_fail_extraction_on_invalid_input(self):
        with self.assertRaises(Exception):
            EventTests.event.extract_arg('22222222')
