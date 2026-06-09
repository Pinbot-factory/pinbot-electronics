# Pinbot lib
The lib written specifically for the **Pinbot r0.2** board and simplifies access to all of its peripherals (relays, LEDs, and the USB hub) over the I2C bus. It also provides convenient access to 16 general-purpose I/O channels. See Pinbot [schematics](../docs/pinbot-carrier-schematic.pdf) for detailed HW architecture.

## Installation and usage
Simply copy the entire directory, including its internal structure and files, to the Raspberry Pi that controls the Pinbot board.

Here is a simple example of using the lib with a Pinbot board.
```python
import pinbot

# Init Pinbot board with it's default periphery config
board = pinbot.init_default()

board.led.on(pinbot.RED)
board.relay.close(1)

board.signal.write(
    "GPIO0",
    state=pinbot.HIGH
)

state = board.signal.read("GPIO0")
print(f"GPIO0 state = {state}")
```

You can find additional usage examples in the repo, along with a couple of tools for debugging your test jigs.

## IO1 signals mapping and pinout
TCA9535  on I2C ddress: **0x20**. General purpose IO expander. Protected GPIO channels (0-24V)

| Port | Pin | Signal Name | Default mode | J2 pin |
|------|-----|-------------|----------------------|---------|
| 0 | 0 | GPIO0 | out | 12 |
| 0 | 1 | GPIO1 | out | 11 |
| 0 | 2 | GPIO2 | out | 14 |
| 0 | 3 | GPIO3 | out | 13 |
| 0 | 4 | GPIO4 | out | 16 |
| 0 | 5 | GPIO5 | out | 15 |
| 0 | 6 | GPIO6 | out | 18 |
| 0 | 7 | GPIO7 | out | 17 |
| 1 | 0 | GPIO8 | out | 22 |
| 1 | 1 | GPIO9 | out | 21 |
| 1 | 2 | GPIO10 | out | 24 |
| 1 | 3 | GPIO11 | out | 23 |
| 1 | 4 | GPIO12 | out | 26 |
| 1 | 5 | GPIO13 | out | 25 |
| 1 | 6 | GPIO14 | out | 28 |
| 1 | 7 | GPIO15 | out | 27 |

## IO2 signals mapping and pinout
TCA9535 on I2C address: **0x21**. Relay control, USB control, alerts and status LEDs.

| Port | Pin | Signal Name | Default mode | Comment |
|------|-----|-------------|--------------|--------|
| 0 | 0 | RELAY1 | out | Relay 1 control, J4 pins 1, 3, 5 |
| 0 | 1 | RELAY2 | out | Relay 2 control, J4 pins 7, 9, 11|
| 0 | 2 | RELAY3 | out | Relay 3 control, J4 pins 13, 15, 17 |
| 0 | 3 | RELAY4 | out | Relay 4 control, J4 pins 19, 21, 23 |
| 0 | 4 | ALERT0 | in | ADS1015 alert 0 |
| 0 | 5 | ALERT1 | in | ADS1015 alert 1 |
| 0 | 6 | USR_R | out | User **red** LED |
| 0 | 7 | USR_G | out | User **green** LED |
| 1 | 0 | USB_FLT1 | in | USB port 1 fault, **active low** |
| 1 | 1 | USB_FLT2 | in | USB port 2 fault, **active low** |
| 1 | 2 | USB_FLT3 | in | USB port 3 fault, **active low** |
| 1 | 3 | USB_FLT4 | in | USB port 4 fault, **active low** |
| 1 | 4 | USB_EN1 | out | USB port 1 enable, **active low** |
| 1 | 5 | USB_EN2 | out | USB port 2 enable, **active low** |
| 1 | 6 | USB_EN3 | out | USB port 3 enable, **active low** |
| 1 | 7 | USB_EN4 | out | USB port 4 enable, **active low** |

Pinbot is a simple library written in Python that works via `smbus2` and `lgpio` (both are included in the standard Raspbian OS distribution). It is suitable for getting familiar with the concept of test jigs and organizing "end-of-line" tests across batches of hundreds and thousands of units. However, do not expect impressive performance or the outstanding stability required for industrial automation.

## TODO
- Proper ADC lib integration
  - More ADC examples
- Example of how to use more than one instance of `pinbot()` in concurent scripts
- Detailed description on USB-hub behaviour
- Implement Active-Low mapping to `pinbot.signal.info()`
- Document whole lib calls
- Ensure USB hub availability in OS