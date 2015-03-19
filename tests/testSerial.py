import unittest
from mock import MagicMock, patch
from copernicus import Copernicus

__author__ = 'gronostaj'


# noinspection PyTypeChecker
class SerialTests(unittest.TestCase):

    @patch('serial.Serial')
    def test_should_create_default_serial(self, serial_mock):
        Copernicus()
        serial_mock.assert_called_once_with('/dev/ttyS0', 38400)

    def test_should_create_custom_serial(self):
        serial_mock = MagicMock()
        Copernicus(serial_mock)
        serial_mock.assert_called_once()

    def test_should_listen_and_handle_bytes(self):
        serial_mock = MagicMock()
        serial_mock.read.return_value = chr(31)
        handle_mock = MagicMock()

        api = Copernicus(serial_mock)
        api.handle = handle_mock
        api.listen()
        handle_mock.assert_called_once_with(chr(31))
