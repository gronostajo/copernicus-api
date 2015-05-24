import unittest
from mock import MagicMock, call
from copernicus import Copernicus

__author__ = 'Krzysztof "gronostaj" Smialek'


class OnDeviceTests(unittest.TestCase):

    def test_should_copy_knob_to_servo(self):
        serial_mock = MagicMock()
        serial_mock.read = MagicMock(side_effect=map(chr, [64, 64 + 32, 64 + 63]))
        serial_mock.write = MagicMock()

        # noinspection PyTypeChecker
        api = Copernicus(connection=serial_mock)

        def knob_handler(value):
            api.command('servo', value / 2)

        api.set_handler('knob', knob_handler)
        api.command('subscribe', 'knob')

        for _ in xrange(3):
            api.listen()

        read_calls = [call(1)] * 3
        serial_mock.read.assert_has_calls(read_calls, True)
        write_calls = map(lambda i: call(chr(i)), [128 + 4, 0, 16, 31])
        serial_mock.write.assert_has_calls(write_calls, True)
