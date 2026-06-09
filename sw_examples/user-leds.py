"""
Example code for Pinbot Control Board user leds
https://github.com/Pinbot-factory
"""
import time
import pinbot

# Initialize board with default configuration
board = pinbot.init_default()

# Turn red LED on
board.led.on(pinbot.RED)
time.sleep(0.5)

# this nitation also valid
# board.led.on("RED")

# Turn red LED off
board.led.off(pinbot.RED)
time.sleep(0.5)

# Toggle green LED a few times
for _ in range(5):
    board.led.toggle(pinbot.GREEN)
    time.sleep(0.2)

# Ensure both user LEDs are off at the end
board.led.off(pinbot.RED)
board.led.off(pinbot.GREEN)