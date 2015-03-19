import unittest
from mock import patch
from copernicus import Copernicus, Event, PatternOverlapError

__author__ = 'gronostaj'


# noinspection PyUnusedLocal
@patch('serial.Serial')
class LoadBitmasksTests(unittest.TestCase):

    def test_should_reject_too_short_mask_test(self, serial_mock):
        api = Copernicus()
        with self.assertRaises(ValueError):
            api.load_events([
                Event('test_7bit', '01_____')
            ])

    def test_should_reject_too_long_mask(self, serial_mock):
        api = Copernicus()
        with self.assertRaises(ValueError):
            api.load_events([
                Event('test_9bit', '10_______')
            ])

    def test_should_reject_bitmask_without_wildcards(self, serial_mock):
        api = Copernicus()
        with self.assertRaises(ValueError):
            api.load_events([
                Event('test_no_wildcards', '01010101')
            ])

    def test_should_reject_bitmask_with_inner_wildcards(self, serial_mock):
        api = Copernicus()
        with self.assertRaises(ValueError):
            api.load_events([
                Event('inner_wildcards', '0011__01')
            ])

    def test_should_accept_regular_bitmasks(self, serial_mock):
        api = Copernicus()
        api.load_events([
            Event('mask1', '0100____'),
            Event('mask2', '1111110_'),
            Event('mask3', '00______'),
            Event('mask4', '1111111_')
        ])

    def test_should_accept_wildcard_only_bitmask(self, serial_mock):
        api = Copernicus()
        api.load_events([
            Event('catch_all', '________')
        ])

    def test_should_reject_overlapping_masks(self, serial_mock):
        api = Copernicus()
        with self.assertRaises(PatternOverlapError):
            api.load_events([
                Event('test1', '0101____'),
                Event('test2', '01010___')
            ])

    def test_should_accept_repeated_names(self, serial_mock):
        api = Copernicus()
        api.load_events([
            Event('test', '0_______'),
            Event('test', '1_______')
        ])
