"""
Example code for Pinbot Control Board usb ports control.
USB hub is always active (check with `lsusb`). User can manage
power on hub's ports (3 USB-A sockets + 1 port as pins on J2)
and handle power erros.
USB ENABLE pins are always "active low" pins.
https://github.com/Pinbot-factory
"""

import time
import pinbot

# Initialize board with default configuration
board = pinbot.init_default()

# Try to enable all USB ports safely
for port in (1, 2, 3, 4):
    try:
        board.usb.enable(port)
        print(f"USB port {port} enabled")
    except pinbot.UsbFaultError as e:
        print(f"Fault detected on port {port}: {e}")

# Check fault status on all ports
for port in (1, 2, 3, 4):
    is_fault = board.usb.is_fault(port)
    print(f"USB port {port} fault state: {is_fault}")

# Delay to let user check a result
time.sleep(5)

# Disable a single port safely
board.usb.disable(2)
print("USB port 2 disabled")

# Enable again with fault handling
try:
    board.usb.enable(2)
    print("USB port 2 re-enabled")
except pinbot.UsbFaultError as e:
    print(f"USB port 2 failed to enable: {e}")

# Final safety ports shutdown
board.usb.disable_all()
print("All USB ports disabled")