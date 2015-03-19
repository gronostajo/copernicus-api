import unittest
from mock import patch, MagicMock
from copernicus import Copernicus, Command, PatternOverlapError, Codecs

__author__ = 'gronostaj'


# noinspection PyUnusedLocal
@patch('serial.Serial')
class CommandsTests(unittest.TestCase):

    def test_should_load_valid_commands(self, serial_mock):
        api = Copernicus()
        api.load_commands({
            'test1': Command('1_______'),
            'test2': Command('0_______')
        })

    def test_should_reject_commands_with_overlapping_masks(self, serial_mock):
        api = Copernicus()
        with self.assertRaises(PatternOverlapError):
            api.load_commands({
                'test1': Command('0_______'),
                'test2': Command('01______')
            })

    def test_should_send_correct_byte(self, serial_mock):
        serial_mock = MagicMock()
        serial_mock.write = MagicMock()

        # noinspection PyTypeChecker
        api = Copernicus(serial_mock)
        api.load_commands({
            'test': Command('11______')
        })
        api.command('test', 1)
        serial_mock.write.assert_called_once_with(chr(193))

    def test_should_fail_on_unknown_command(self, serial_mock):
        api = Copernicus()
        api.load_commands({
            'cmd': Command('1_______')
        })
        with self.assertRaises(KeyError):
            api.command('unknown')

    def test_should_encode_single_services_correctly(self, serial_mock):
        self.assertEqual(Codecs.encode_services('light'), 32)
        self.assertEqual(Codecs.encode_services('button1'), 16)
        self.assertEqual(Codecs.encode_services('button2'), 8)
        self.assertEqual(Codecs.encode_services('knob'), 4)
        self.assertEqual(Codecs.encode_services('temperature'), 2)
        self.assertEqual(Codecs.encode_services('motion'), 1)

    def test_should_encode_star_service_correctly(self, serial_mock):
        self.assertEqual(Codecs.encode_services('*'), 32 + 16 + 8 + 4 + 2 + 1)

    def test_should_or_values_correctly(self, serial_mock):
        self.assertEqual(Codecs.encode_services('light', 'motion'), 32 + 1)
        self.assertEqual(Codecs.encode_services('light', '*'), 32 + 16 + 8 + 4 + 2 + 1)

    def test_should_encode_rgb_correctly(self, serial_mock):
        self.assertEqual(Codecs.encode_rgb(1, 2, 3), 1 * 16 + 2 * 4 + 3)

    def test_should_decode_color_names_correctly(self, serial_mock):
        self.assertEqual(Codecs.encode_rgb('off'), 0)
        self.assertEqual(Codecs.encode_rgb('red'), 3 * 16)
        self.assertEqual(Codecs.encode_rgb('green'), 3 * 4)
        self.assertEqual(Codecs.encode_rgb('blue'), 3)
        self.assertEqual(Codecs.encode_rgb('cyan'), 3 * 4 + 3)
        self.assertEqual(Codecs.encode_rgb('magenta'), 3 * 16 + 3)
        self.assertEqual(Codecs.encode_rgb('yellow'), 3 * 16 + 3 * 4)
        self.assertEqual(Codecs.encode_rgb('white'), 3 * 16 + 3 * 4 + 3)