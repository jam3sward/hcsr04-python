# hcsr04-python
HCSR04 Python Module for Raspberry Pi

This module provides a convenient way to interface with the ubiquitous HC-SR04 Ultrasonic Distance Sensor on the Raspberry Pi. To use it, create an instance of the hcsr04.Ranger class, passing the GPIO pin numbers for the trigger output pin and the echo input pin. You can then call getRange() to obtain a range measurement (in metres). When finished, call cleanup() to free the resources. You can also use the setSpeedOfSound() function to change the speed of sound used in the distance calculations.

In order to access the GPIO pins it requires the PIPGPIO Python Module (https://github.com/joan2937/pigpio)
