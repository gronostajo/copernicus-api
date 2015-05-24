from __future__ import print_function

import re
import operator
import serial
import sys

__author__ = 'Krzysztof "gronostaj" Smialek'
__all__ = ['Copernicus']


class PatternOverlapError(Exception):
    def __init__(self, msg, pattern1, pattern2):
        super(PatternOverlapError, self).__init__(msg)
        self.pattern1 = pattern1
        self.pattern2 = pattern2


class BitPattern:

    def __init__(self, mask):
        """
        :type mask: str
        """
        if len(mask) != 8 or not re.match('^[01]*_+$', mask):
            raise ValueError('`{0}` is not a valid 8-bit mask'.format(mask))
        self._mask = mask
        self._low = int(mask.replace('_', '0'), 2)
        self._high = int(mask.replace('_', '1'), 2)
        self._masked_bits = mask.count('_')

    @property
    def mask(self):
        return self._mask

    @property
    def masked_bits(self):
        return self._masked_bits

    @property
    def bounds(self):
        return self._low, self._high

    def matches(self, bits):
        """
        :type bits: str
        """
        value = int(bits, 2)
        return self._low <= value <= self._high

    def is_subset_of(self, pattern):
        """
        :type pattern: BitPattern
        """
        known_bits = 8 - pattern.masked_bits
        return self._mask[:known_bits] == pattern.mask[:known_bits]

    @staticmethod
    def assert_no_overlaps(patterns):
        """
        :type patterns: list[BitPattern]
        """
        patterns = sorted(patterns, key=lambda pattern_: pattern_.masked_bits, reverse=True)
        for index, pattern in enumerate(patterns):
            for following_pattern in patterns[index + 1:]:
                if following_pattern.is_subset_of(pattern):
                    raise PatternOverlapError('Pattern {0} overlaps with {1}'.format(following_pattern.mask, pattern.mask), following_pattern, pattern)


class Event:

    def __init__(self, name, mask, transform=None):
        """
        :type name: str
        :type mask: str
        :type transform: (int) -> T
        """
        self._name = name
        self._pattern = BitPattern(mask)
        self._transform = transform if transform is not None else lambda x: x

    @property
    def name(self):
        return self._name

    @property
    def pattern(self):
        return self._pattern

    def transform(self, value):
        """
        :type value: int
        :rtype int
        """
        return self._transform(value)

    def extract_arg(self, bits):
        """
        :type bits: str
        :rtype int
        """
        if not self._pattern.matches(bits):
            raise ValueError()
        masked_bits = bits[-self._pattern.masked_bits:]
        return int(masked_bits, 2)


class Command:

    def __init__(self, mask, transform=None):
        self._pattern = BitPattern(mask)
        self._transform = transform if transform is not None else lambda x: x

    @property
    def pattern(self):
        return self._pattern

    def translate(self, *args):
        """
        :type args: list[int]
        :rtype chr
        """
        value = self._transform(*args)
        binary = "{0:b}".format(value).zfill(self._pattern.masked_bits)
        if len(binary) > self._pattern.masked_bits:
            raise ValueError("Value too big")
        cmd_string = re.sub('_+', binary, self._pattern.mask)
        return chr(int(cmd_string, 2))
    
    
class Codecs:
    
    def __init__(self):
        pass

    _available_events = {
        'motion': 1,
        'temperature': 2,
        'knob': 4,
        'button2': 8,
        'button1': 16,
        'light': 32,
        '*': 63
    }
    
    @staticmethod
    def encode_services(*args):
        int_values = map(lambda evt: Codecs._available_events[evt], args)
        return reduce(operator.or_, int_values)
    
    @staticmethod
    def encode_rgb(*args):
        color_names = {
            'off': 0,
            'red': 48,
            'green': 12,
            'blue': 3,
            'cyan': 15,
            'magenta': 51,
            'yellow': 60,
            'white': 63
        }
        if len(args) == 1:
            return color_names[args[0]]
        else:
            return args[0] * 16 + args[1] * 4 + args[2]
        
    @staticmethod
    def decode_temperature(temp):
        return temp / 2.0 + 10
    

class Copernicus:

    _default_events = [
        Event('light', '00______'),
        Event('knob', '01______'),
        Event('temperature', '10______', Codecs.decode_temperature),
        Event('motion', '1100000_', bool),
        Event('button1', '1100001_', bool),
        Event('button2', '1100010_', bool)
    ]

    _default_commands = {
        'servo': Command('000_____'),
        'led': Command('0010000_', int),
        'rgb': Command('01______', Codecs.encode_rgb),
        'subscribe': Command('10______', Codecs.encode_services),
        'query': Command('11______', Codecs.encode_services)
    }

    def __init__(self, timeout=None, connection=None, debug=False):
        """
        Creates a new Copernicus API object and loads default events and commands.
        :param timeout: Serial connection timeout for listen() calls. Either this of connection arg must be None.
        :param connection: Serial object to use for communication with Copernicus.
        :type connection: serial.Serial
        """
        self._debug = debug
        assert timeout is None or connection is None

        if timeout is not None and \
                type(timeout) is not int and type(timeout) is not float and \
                type(timeout) is type(serial.Serial()):
            print('Warning: You\'re using the old API call. Instead of this:', file=sys.stderr)
            print('    api = Copernicus(my_conn)', file=sys.stderr)
            print('Use this:', file=sys.stderr)
            print('    api = Copernicus(connection=my_conn)', file=sys.stderr)
            connection = timeout

        if connection is None:
            self._connection = serial.Serial('/dev/ttyS0', 38400, timeout=timeout)
        else:
            self._connection = connection

        self._events = []
        self._handlers = {}
        self._default_handler = None
        self._commands = {}

        self.load_events(self._default_events)
        self.load_commands(self._default_commands)

    def load_events(self, events):
        """
        Loads new event set that is later used to translate serial responses to API events.
        Event set is simply a list of Event objects.
        Calling this method discards all previously registered handlers.
        :type events: list[Event]
        """
        patterns = [event.pattern for event in events]
        BitPattern.assert_no_overlaps(patterns)
        self._events = events
        self._handlers = dict((event.name, None) for event in events)

    def set_handler(self, event, handler):
        """
        Registers a handler function for event. This function will be supplied with an argument extracted from serial
        response and called each time event is fired. Overwrites previously registered handler.
        :param event: Name of event that should be handled with this function
        :param handler: Function that can handle this event
        :type event: str
        :type handler: (T) -> None
        """
        if event not in self._handlers:
            raise ValueError('Unknown event `{0}`'.format(event))
        self._handlers[event] = handler

    def set_default_handler(self, handler):
        """
        Registers a catch-all handler. This handler is called each time a recognized event fires, but no event-specific
        handler is registered. Default handler is supplied with event's name and extracted argument.
        :param handler: Function that should handle events by default
        :type handler: (str, T) -> None
        """
        self._default_handler = handler

    def handle(self, value):
        """
        Finds a correct event handler that should fire for provided value and calls it with appropriate argument.
        :param value: Single byte received from serial device
        :type value: chr
        """
        value = ord(value)
        bin_value = '{0:b}'.format(value)
        this_event = None
        for event in self._events:
            if event.pattern.matches(bin_value):
                this_event = event
                break
        if this_event is None:
            raise KeyError('Unrecognized byte value {0}'.format(value))

        event = this_event
        arg = this_event.extract_arg(bin_value)
        if self._handlers[event.name] is not None:
            translated_arg = event.transform(arg)
            self._handlers[event.name](translated_arg)
        elif self._default_handler is not None:
            self._default_handler(event.name, arg)

    def listen(self):
        """
        Waits for incoming byte and fires appropriate event.
        :return: Whether event was received (True) or read operation timed out (False).
        :rtype: bool
        """
        char = self._connection.read(1)
        if len(char) > 0:
            if self._debug:
                print('Byte received: {0:b}'.format(ord(char)))
            self.handle(char)
            return True
        else:
            if self._debug:
                print('Timed out')
            return False

    def load_commands(self, commands):
        """
        Loads new Copernicus command set that is later used to translate API commands to serial queries.
        :param commands: A dict with command names as keys and Command objects as values
        :type commands: dict[str, Command]
        """
        patterns = map(lambda cmd: cmd.pattern, commands.values())
        BitPattern.assert_no_overlaps(patterns)
        self._commands = commands

    def command(self, cmd, *args):
        """
        Sends a serial command to Copernicus.
        :param cmd: Name of command to be sent
        :param args: Any number of arguments. Accepted arguments differ between commands.
        :type cmd: str
        :type args: list[*]
        """
        if cmd not in self._commands:
            raise KeyError('Unknown command {0}'.format(cmd))
        char = self._commands[cmd].translate(*args)
        self._connection.write(char)
        if self._debug:
            print('Byte sent: {0:b}'.format(ord(char)))
