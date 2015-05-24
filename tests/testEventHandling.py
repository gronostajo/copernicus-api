import unittest
from mock import MagicMock
from copernicus import Copernicus, Event


__author__ = 'Krzysztof "gronostaj" Smialek'


class EventHandlingTests(unittest.TestCase):
    @staticmethod
    def get_api():
        # noinspection PyTypeChecker
        api = Copernicus(connection=MagicMock())
        api.load_events([
            Event('case1', '1_______'),
            Event('case0', '0_______')
        ])
        return api

    def test_should_fire_correct_handler(self):
        api = EventHandlingTests.get_api()
        handler = MagicMock()
        api.set_handler('case0', handler)
        api.handle(chr(int('01111111', 2)))
        handler.assert_called_once_with(127)

    def test_should_not_file_incorrect_handler(self):
        api = EventHandlingTests.get_api()
        handler = MagicMock(side_effect=Exception('Invalid handler called'))
        api.set_handler('case0', handler)
        api.handle(chr(int('10000000', 2)))

    def test_should_call_default_handler(self):
        api = EventHandlingTests.get_api()
        handler = MagicMock()
        api.set_default_handler(handler)
        api.handle(chr(int('11000000', 2)))
        handler.assert_called_once_with('case1', 64)

    def test_should_not_call_default_handler_if_specific_is_available(self):
        api = EventHandlingTests.get_api()
        default_handler = MagicMock(side_effect=Exception('Default handler called'))
        api.set_handler('case0', MagicMock())
        api.set_default_handler(default_handler)
        api.handle(chr(int('00000011', 2)))

    def test_should_fail_on_unknown_event(self):
        # noinspection PyTypeChecker
        api = Copernicus(connection=MagicMock())
        api.load_events([])
        with self.assertRaises(KeyError):
            api.handle(chr(int('00000000', 2)))

    def test_should_decode_temperature_correctly(self):
        serial_mock = MagicMock()
        serial_mock.read = MagicMock(return_value=chr(151))
        # noinspection PyTypeChecker
        api = Copernicus(connection=serial_mock)

        handler = MagicMock()
        api.set_handler('temperature', handler)
        api.listen()
        handler.assert_called_once_with(21.5)
