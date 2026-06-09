"""
Example code for switching Pinbot Control Board relays
https://github.com/Pinbot-factory
"""
import time
import pinbot

# Initialize board with default configuration
board = pinbot.init_default()

# Make sure all relays are initially "OFF" — in normal closed (NC) state
board.relay.close_all()
time.sleep(1)

# Turn relay 1 "ON": NC → NO
board.relay.open(1)
time.sleep(0.5)

# Turn relay 1 "OFF": NO → NC
board.relay.close(1)
time.sleep(0.5)

# Cycle through all relays one by one
for relay_id in (1, 2, 3, 4):
    board.relay.open(relay_id)
    time.sleep(0.2)
    board.relay.close(relay_id)
    time.sleep(0.2)

# Open and close all
board.relay.open_all()
time.sleep(0.5)
board.relay.close_all()