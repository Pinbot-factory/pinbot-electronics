"""
Example of using Pinbot Control Board relays
not for QA but for clicky sounds
https://github.com/Pinbot-factory
"""
import time
import pinbot

board = pinbot.init_default()

board.relay.close_all()
time.sleep(1)


def click(relay_id):
    # relay open → short delay → close it back
    board.relay.open(relay_id)
    time.sleep(0.05)
    board.relay.close(relay_id)


sequence = [
    (1, 0.2),
    (2, 0.2),
    (3, 0.2),
    (2, 0.2),

    (4, 0.4),
    (3, 0.2),
    (2, 0.2),
    (1, 0.4),

    (1, 0.2),
    (2, 0.2),
    (3, 0.2),
    (2, 0.2),

    (4, 0.4),
    (3, 0.2),
    (2, 0.2),
    (1, 0.6),
]

for relay_id, pause in sequence:
    click(relay_id)
    time.sleep(pause)

board.relay.close_all()

print("Done. What was the melody?")