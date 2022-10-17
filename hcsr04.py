import pigpio
import time

# The HCSR04 Python Module provides a convenient way to interface with the
# ubiquitous HC-SR04 Ultrasonic Distance Sensor. To use it, create an instance
# of the hcsr04.Ranger class, passing the GPIO pin numbers for the trigger
# output pin and the echo input pin. You can then call getRange() to obtain a
# range measurement (in metres). When finished, call cleanup() to free the
# resources. You can also use the setSpeedOfSound() function to change the
# speed of sound used in the distance calculations.
#
# Copyright (C) 2022 James Ward
# Released under an MIT License

# Dependencies:
#   Requires the PIPGPIO Python Module (https://github.com/joan2937/pigpio)

# Example code:
#   import hcsr04
#   triggerOutputPin = 23
#   echoInputPin = 24
#   ranger = hcsr04.Ranger(triggerOutputPin, echoInputPin)
#   print(ranger.getRange())
#   ranger.cleanup()

# the default speed of sound in metres per second
_SPEED_OF_SOUND = 343

# the maximum range of the HC-SR04 in metres
_MAXIMUM_RANGE = 4

# maximum echo time expected in seconds
_MAXIMUM_ECHO_TIME = 2 * _MAXIMUM_RANGE / _SPEED_OF_SOUND

# maximum time period between ranging triggers
_MAXIMUM_RANGE_TIME = _MAXIMUM_ECHO_TIME * 1.1

# this dictionary maps GPIO echo input pins to the associated Ranger instance
# edgeCallback. we use it to forward edge events to the Ranger class instance
_edgeEventHandlers = {}

# this is our global edge callback function which we register with PIGPIO
def _globalEdgeCallback(gpio, level, ticks):
    # forward the event to the associated Ranger class instance
    if gpio in _edgeEventHandlers:
        _edgeEventHandlers[gpio](level, ticks)
    else:
        print("unhandled edgeCallback(", gpio, level, ticks, ")")

# An instance of this class represents a single HC-SR04
# Ultrasonic ranger.
class Ranger:

    # set the speed of sound in metres per second
    # this is used when calculating the range from the echo pulse time
    def setSpeedOfSound(self, speed):
        self.__speedOfSound = speed

    # returns the currently set speed of sound in metres per second
    def getSpeedOfSound(self):
        return self.__speedOfSound

    # takes a single range measurement and returns the received echo
    # pulse width in microseconds (may return 0 in case of error)
    # use getRange() instead if you want the distance in metres
    def getRangePulseWidth(self):
        # send 10us trigger pulse
        self.__gpio.gpio_trigger(self.__triggerOutputPin, 10, 1);

        # wait until we either get an echo pulse, or we reached the
        # maximum expected ranging time interval
        stopTime = time.time() + _MAXIMUM_RANGE_TIME
        while self.__elapsedTicks == 0 and time.time() < stopTime:
            time.sleep(_MAXIMUM_RANGE_TIME / 10)

        # return the pulse width in microseconds
        return self.__elapsedTicks

    # takes a single range measurement and returns the distance in metres,
    # the normal valid range is between 0 to 4m, but this may return larger
    # values if there is no response detected
    def getRange(self):
        # convert the ticks in microseconds to a distance in metres
        return self.__speedOfSound * self.getRangePulseWidth() / 2e6

    # called for the rising and falling edge of the echo pulse
    def __edgeCallback(self, level, ticks):
        if level == 1:
            # store ticks at rising echo pulse edge
            self.__initialTicks = ticks
        elif self.__initialTicks > 0:
            # calculate echo pulse width at falling pulse edge
            self.__elapsedTicks = pigpio.tickDiff(self.__initialTicks, ticks)
            self.__initialTicks = 0

    # the constructor
    def __init__(self, triggerOutputPin, echoInputPin):
        # initialise PIGPIO
        self.__gpio = pigpio.pi()
        
        # set the default speed of sound
        self.__speedOfSound = _SPEED_OF_SOUND

        # store our trigger/echo pin numbers
        self.__triggerOutputPin = triggerOutputPin
        self.__echoInputPin = echoInputPin

        # setup range finder
        self.__gpio.set_mode(self.__triggerOutputPin, pigpio.OUTPUT)
        self.__gpio.set_mode(self.__echoInputPin, pigpio.INPUT)
        self.__gpio.write(self.__triggerOutputPin, 0)
        time.sleep(_MAXIMUM_ECHO_TIME);

        # we use these member variables to measure the echo pulse width
        self.__initialTicks = 0
        self.__elapsedTicks = 0

        # register ourself to receive callbacks for the rising and falling
        # edges of the echo pulse
        _edgeEventHandlers[self.__echoInputPin] = self.__edgeCallback

        # connect the echo input pin to the global edge callback function
        # this will get called for the rising and falling edges of all echo pulses
        self.__edgeCallback = self.__gpio.callback(self.__echoInputPin, pigpio.EITHER_EDGE, _globalEdgeCallback)

    # call this when you are finished with the Ranger in order to release
    # the various resources and GPIO pins it was using
    def cleanup(self):
        # cancel the edge callback
        if self.__edgeCallback:
            self.__edgeCallback.cancel()
            self.__edgeCallback = None

        # revert the trigger output pin to an input for safety
        self.__gpio.set_mode(self.__triggerOutputPin, pigpio.INPUT)

        # remove ourself from the event handler dictionary
        if self.__echoInputPin in _edgeEventHandlers:
            _edgeEventHandlers.pop(self.__echoInputPin)

        # we are finished with pigpio
        if self.__gpio:
            self.__gpio.stop()
            self.__gpio = None

