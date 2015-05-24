# Copernicus API for Python

Convenient, high-level interface for [AGH Copernicus](http://home.agh.edu.pl/~tszydlo/copernicus/).

This library is an independent work. It is not officially supported by creators of Copernicus.

## About

Copernicus API is a high-level wrapper for Copernicus' serial mode. Instead of relying on magic numbers and complex chains of if-else conditions, API enables developer to write clean, self-describing code.

Here's a sample program that continuously sets servo's direction depending on knob's position written without API:

    import serial

    ser = serial.Serial('/dev/ttyS0', 38400)

    ser.write(chr(128 + 4))

    while True:
        knob = ord(ser.read(1)) - 64
        if 0 <= knob < 64:
            servo = knob / 2
            ser.write(chr(servo)) 

Here's the same program, this time built on Copernicus API:

    from copernicus import Copernicus

    api = Copernicus()

    def rotate_servo(pos):
        api.command('servo', pos / 2)

    api.command('subscribe', 'knob')
    api.set_handler('knob', rotate_servo)

    while True:
        api.listen()

## Initialization

To create a connection with Copernicus, simply create a Copernicus object:

    from copernicus import Copernicus
    api = Copernicus()

If you don't like default serial connection (`ttyS0`, 38400 bd), you can supply your own one:

    api = Copernicus(connection=MyCustomSerial())

## Commands

This library wraps Copernicus' query/response interface with more convenient commands and events API.

Commands map directly to 1-byte queries, but are more like regular function calls. A command can be called at any time like this:

    api.command('command_name', arg1, arg2, ...)

Note that there are no magic numbers. Commands are identified by names and can be supplied with multiple arguments, possibly non-byte ones too.

Following commands are available by default:

- `servo <0-31>`
- `led <True|False>`
- `rgb <0-3> <0-3> <0-3>` (R, G, B values)
- `rgb 'color_name'` (list of color names below)
- `subscribe 'event1' 'event2' 'event3'...` (any number of supported events or `*` to subscribe to all)
- `query 'event_name'`

Supported color names are: `off`, `red`, `green`, `blue`, `cyan`, `magenta`, `yellow`, `white`

Here's an example of sending few commands:

    api.command('servo', 16)        # set servo in the middle position
    api.command('rgb', 1, 0, 0)     # set RGB LED to faint red
    api.command('led', False)       # turn off non-RGB led
    api.command('subscribe', '*')   # subscribe to all events

## Events

API provides event-driven interface for Copernicus. Incoming events are translated to Python function calls, including argument translation. By default, following events are available:

- `light` (0 - 63)
- `knob` (0 - 63)
- `temperature` (10 - 41.5, resolution=0.5)
- `motion` (True/False)
- `button1` (True/False)
- `button2` (True/False)

Events are received either as a reply to a `query` command or as a result of `subscribe` command. `listen()` method causes program to wait for an event, then handle it and continue execution.

    while True:
        api.listen()  # handle any events

Each type of event can be assigned a handler function that will receive one argument: response's value.

    def button_handler(state):
        print 'Pressed' if state else 'Released'

    api.set_handler('button1', button_handler)
    api.set_handler('button2', button_handler)

    while True:
        api.listen()

Moreover, a default handler can be defined that will be called if event-specific handler is not available. Default handler is called with event's name and response's value.

    def handler(event_name, state):
        if event_name[:6] == 'button':
            state_str = 'pressed' if state else 'released'
            print event_name, state_str

    api.set_default_handler(handler)

    while True:
        api.listen()


## Non-blocking listening

`listen()` blocks until an event is received. If you want to simulate non-blocking listening, use constructor with the `timeout` argument:

    api = Copernicus(timeout=0.1)
    
This will make `listen()` timeout every 1/10th of a second if no command is received, so the listening loop will unblock at least 10 times every second to process queued operations:

    while True:
        api.listen()  # This lasts 0.1s or less if event is received, then
                      # queued operations are executed and the loop repeats

For example this program will toggle LED ten times a second or as soon as any event is received:

    api = Copernicus(timeout=0.1)
    led_state = False

    while True:
        led_state = not led_state
        api.command('led', led_state)
        api.listen()
        
`listen()` returns `True` if listening ends due to incoming event, or `False` if listening times out.

Do not rely on `listen()` timeouts for time counting, as incoming events can cause `listen()` to return prematurely.
