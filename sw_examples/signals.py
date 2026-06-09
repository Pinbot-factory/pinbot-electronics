"""
Example code for pins management with Pinbot Control
Board IO expanders (TCA9535).
Check board schematics and README.md on pinout
and default pins configuration and names
https://github.com/Pinbot-factory
"""

import time
import pinbot

# Initialize board with default configuration
board = pinbot.init_default()

# Write HIGH to a GPIO1 signal
board.signal.write(
    "GPIO1",
    state=pinbot.HIGH,
    mode="out",
    inverted=False
)
# While some of parameters optional,
# you can achieve same result with shorter
# board.signal.write("GPIO1", "HIGH")
# or even
# board.signal.write("GPIO1", 1)

time.sleep(0.5)

# Read back the signal state
state = board.signal.read("GPIO1")
print("GPIO1 state:", state)

# Get detailed info about the signal
# like latch state, pin mode, inversion
info = board.signal.info("GPIO1")
print("GPIO1 info:", info)

time.sleep(1)

# Write LOW to the same signal
board.signal.write(
    "GPIO01",
    state=pinbot.LOW
)

# Read again after change
state = board.signal.read("GPIO01")
print("GPIO01 state after LOW:", state)

# It's possible to use SignalControl class to manage
# pins of both TCA ICs. So relays, leds and USB ports (active LOW)
# are available to manage too
board.signal.write("usr_red", 1)
board.signal.write("relay1", 1)
time.sleep(0.5)
board.signal.write("relay1", 0)
board.signal.write("usr_red", 0)
