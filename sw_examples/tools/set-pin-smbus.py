"""
Debug helper to manipulate Pinbot pins thru pure smbus
Works only with TCA on 0x21, some pins configured as INPUTS
TCA address, Port, Pin, State
usage example:
    python3 set-pin.py 0x21 0 3 1
https://github.com/Pinbot-factory
"""

import argparse
from smbus2 import SMBus


# TCA9535 registers
OUTPUT_PORT_0 = 0x02
OUTPUT_PORT_1 = 0x03

CONFIG_PORT_0 = 0x06
CONFIG_PORT_1 = 0x07

I2C_BUS = 1


def parse_address(value):
    """
    Allow address formats:
    0x20
    20
    """
    return int(value, 16)


parser = argparse.ArgumentParser(
    description="Set TCA9535 pin state"
)

parser.add_argument(
    "address",
    type=parse_address,
    help="I2C address (example: 0x20)"
)

parser.add_argument(
    "port",
    type=int,
    choices=[0, 1],
    help="Port number: 0 or 1"
)

parser.add_argument(
    "pin",
    type=int,
    choices=range(8),
    help="Pin number: 0-7"
)

parser.add_argument(
    "state",
    type=int,
    choices=[0, 1],
    help="Pin state: 0 or 1"
)

args = parser.parse_args()

output_reg = OUTPUT_PORT_0 if args.port == 0 else OUTPUT_PORT_1
config_reg = CONFIG_PORT_0 if args.port == 0 else CONFIG_PORT_1

pin_mask = 1 << args.pin

with SMBus(I2C_BUS) as bus:

    #
    # Initial configuration:
    # Port 1 pins 0,1,2,3 = INPUT
    #
    config_p1 = bus.read_byte_data(args.address, CONFIG_PORT_1)

    # 1 = input
    config_p1 |= 0b00001111

    bus.write_byte_data(args.address, CONFIG_PORT_1, config_p1)

    #
    # Configure selected pin as output
    #
    config = bus.read_byte_data(args.address, config_reg)

    # 0 = output
    config &= ~pin_mask

    bus.write_byte_data(args.address, config_reg, config)

    #
    # Update output state
    #
    output = bus.read_byte_data(args.address, output_reg)

    if args.state:
        output |= pin_mask
    else:
        output &= ~pin_mask

    bus.write_byte_data(args.address, output_reg, output)

print(
    f"Set TCA9535 0x{args.address:02X} "
    f"P{args.port}_{args.pin} = {args.state}"
)