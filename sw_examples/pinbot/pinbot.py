"""
Pinbot Board Control Library.
"""

import logging
import time
from .tca9535 import *

try:
    import lgpio
    LGPIO_AVAILABLE = True
except ImportError:
    LGPIO_AVAILABLE = False


class RelayControl:
    """
    Control helper for Pinbot relays.
    Relays 1-4 are mapped to io2 Port 0 Pins 0-3.
    """
    def __init__(self, board):
        self.board = board

    def open(self, relay_id):
        """
        Open (energize/turn on) a relay by setting the pin to HIGH.
        """
        if relay_id not in (1, 2, 3, 4):
            raise ValueError("Relay ID must be 1, 2, 3, or 4")
        pin = relay_id - 1
        self.board.io2.digital_write(0, pin, HIGH)

    def close(self, relay_id):
        """
        Close (de-energize/turn off) a relay by setting the pin to LOW.
        """
        if relay_id not in (1, 2, 3, 4):
            raise ValueError("Relay ID must be 1, 2, 3, or 4")
        pin = relay_id - 1
        self.board.io2.digital_write(0, pin, LOW)

    def open_all(self):
        """
        Open all 4 relays.
        """
        for relay_id in (1, 2, 3, 4):
            self.open(relay_id)

    def close_all(self):
        """
        Close all 4 relays.
        """
        for relay_id in (1, 2, 3, 4):
            self.close(relay_id)


# LED Constants
RED = "red"
GREEN = "green"


class LedControl:
    """
    Control helper for Pinbot user LEDs.
    Red LED is mapped to io2 Port 0 Pin 6.
    Green LED is mapped to io2 Port 0 Pin 7.
    """
    def __init__(self, board):
        self.board = board

    def _get_pin(self, led_id):
        if not isinstance(led_id, str):
            raise TypeError("LED ID must be a string ('RED' or 'GREEN')")
        norm_id = led_id.lower()
        if norm_id == "red":
            return 6
        elif norm_id == "green":
            return 7
        else:
            raise ValueError(f"Invalid LED ID: {led_id}. Must be 'RED' or 'GREEN'")

    def on(self, led_id):
        """
        Turn ON the specified LED.
        """
        pin = self._get_pin(led_id)
        self.board.io2.digital_write(0, pin, HIGH)

    def off(self, led_id):
        """
        Turn OFF the specified LED.
        """
        pin = self._get_pin(led_id)
        self.board.io2.digital_write(0, pin, LOW)

    def toggle(self, led_id):
        """
        Toggle the state of the specified LED.
        """
        pin = self._get_pin(led_id)
        # Read the current latch state from the shadow register cache
        current_state = (self.board.io2.get_output_port(0) >> pin) & 1
        new_state = LOW if current_state == HIGH else HIGH
        self.board.io2.digital_write(0, pin, new_state)


class UsbFaultError(Exception):
    """
    Exception raised when a USB port experiences a fault condition.
    """
    pass


class UsbControl:
    """
    Control helper for Pinbot USB Ports (Ports 1-4).
    Enables/disables ports and monitors fault status (active-low).
    """
    def __init__(self, board):
        self.board = board
        self.fault_occurred = [False, False, False, False, False]

    def _validate_port(self, port):
        if port not in (1, 2, 3, 4):
            raise ValueError("USB Port must be 1, 2, 3, or 4")

    def _get_pins(self, port):
        # EN is on Port 1, Pins 4-7
        # FLT is on Port 1, Pins 0-3
        en_pin = port + 3
        flt_pin = port - 1
        return en_pin, flt_pin

    def is_fault(self, port):
        """
        Check if a fault is active on the specified USB port.
        Since FLT is active-low, a fault is active when pin state is LOW (0).
        """
        self._validate_port(port)
        _, flt_pin = self._get_pins(port)
        return self.board.io2.digital_read(1, flt_pin) == LOW

    def enable(self, port):
        """
        Enable the specified USB port (active-low, write LOW).
        Raises UsbFaultError if a fault condition is detected immediately.
        """
        self._validate_port(port)
        en_pin, _ = self._get_pins(port)
        self.fault_occurred[port] = False

        # Enable by writing LOW (0)
        self.board.io2.digital_write(1, en_pin, LOW)

        # Give the overcurrent protection circuit (MIC2026) a tiny window (20ms)
        # to charge capacitors and trigger USB_FLT if there is a short circuit.
        time.sleep(0.02)

        # Check if a fault is active
        if self.is_fault(port):
            # Disable port immediately for safety
            self.disable(port)
            raise UsbFaultError(f"USB port {port} fault detected upon enablement")

    def disable(self, port):
        """
        Disable the specified USB port (active-low, write HIGH).
        """
        self._validate_port(port)
        en_pin, _ = self._get_pins(port)
        self.fault_occurred[port] = False

        # Disable by writing HIGH (1)
        self.board.io2.digital_write(1, en_pin, HIGH)

    def enable_all(self):
        """
        Enable all 4 USB ports.
        Raises UsbFaultError if any port faults during activation.
        """
        for port in (1, 2, 3, 4):
            self.enable(port)

    def disable_all(self):
        """
        Disable all 4 USB ports.
        """
        for port in (1, 2, 3, 4):
            self.disable(port)


class SignalControl:
    """
    Unified signal control abstraction. Mapping logic names to physical expander pins.
    """
    def __init__(self, board):
        self.board = board
        # Map lower-case signal name to (TCA attribute name, port, pin)
        self._mapping = {}

        # Register TCA1 signals (GPIO00 to GPIO15)
        for i in range(16):
            port = i // 8
            pin = i % 8
            # Register multiple aliases
            aliases = [
                f"gpio{i}",
                f"gpio{i:02d}",
            ]
            for alias in aliases:
                self._mapping[alias] = ("io1", port, pin)

        # Register TCA2 signals (Relays, Alerts, LEDs, USB)
        # Port 0
        for i in range(4):
            relay_num = i + 1
            self._mapping[f"relay{relay_num}"] = ("io2", 0, i)
            self._mapping[f"relay_{relay_num}"] = ("io2", 0, i)

        self._mapping["alert0"] = ("io2", 0, 4)
        self._mapping["alert_0"] = ("io2", 0, 4)
        self._mapping["alert1"] = ("io2", 0, 5)
        self._mapping["alert_1"] = ("io2", 0, 5)

        self._mapping["usr_r"] = ("io2", 0, 6)
        self._mapping["usr_red"] = ("io2", 0, 6)
        self._mapping["red_led"] = ("io2", 0, 6)
        self._mapping["red"] = ("io2", 0, 6)

        self._mapping["usr_g"] = ("io2", 0, 7)
        self._mapping["usr_green"] = ("io2", 0, 7)
        self._mapping["green_led"] = ("io2", 0, 7)
        self._mapping["green"] = ("io2", 0, 7)

        # Port 1
        for i in range(4):
            port_num = i + 1
            self._mapping[f"usb_flt{port_num}"] = ("io2", 1, i)
            self._mapping[f"usb_flt_{port_num}"] = ("io2", 1, i)
            self._mapping[f"usb_en{port_num}"] = ("io2", 1, i + 4)
            self._mapping[f"usb_en_{port_num}"] = ("io2", 1, i + 4)

    def _resolve_signal(self, name):
        if not isinstance(name, str):
            raise TypeError("Signal name must be a string")
        norm_name = name.lower().strip()
        if norm_name not in self._mapping:
            raise KeyError(f"Unknown signal name: '{name}'")
        return self._mapping[norm_name]

    def read(self, signal_name):
        """
        Read the physical level of the specified signal pin.
        """
        tca_attr, port, pin = self._resolve_signal(signal_name)
        tca = getattr(self.board, tca_attr)
        return tca.digital_read(port, pin)

    def write(self, signal_name, state, mode=None, inverted=None):
        """
        Write the state of the specified signal, optionally configuring mode and polarity.
        """
        tca_attr, port, pin = self._resolve_signal(signal_name)
        tca = getattr(self.board, tca_attr)

        # Resolve state representation to 0 or 1
        if isinstance(state, str):
            norm_state = state.strip().lower()
            if norm_state == "high":
                state_val = HIGH
            elif norm_state == "low":
                state_val = LOW
            else:
                raise ValueError(f"Invalid state string: '{state}'. Must be 'HIGH' or 'LOW'")
        else:
            state_val = HIGH if state else LOW

        if mode is not None:
            if not isinstance(mode, str):
                raise TypeError("mode must be a string ('in' or 'out')")
            mode_val = mode.lower()
            if mode_val == "in":
                tca.pin_mode(port, pin, INPUT)
            elif mode_val == "out":
                tca.pin_mode(port, pin, OUTPUT)
            else:
                raise ValueError("mode must be 'in' or 'out'")

        if inverted is not None:
            tca.set_polarity_inversion(port, pin, bool(inverted))

        tca.digital_write(port, pin, state_val)

    def info(self, signal_name):
        """
        Return status information dictionary for the specified signal.
        """
        tca_attr, port, pin = self._resolve_signal(signal_name)
        tca = getattr(self.board, tca_attr)

        state = tca.digital_read(port, pin)
        latch = (tca.output[port] >> pin) & 1
        config_bit = (tca.config[port] >> pin) & 1
        mode = "in" if config_bit == 1 else "out"
        inverted = ((tca.polarity[port] >> pin) & 1) == 1

        return {
            "state": state,
            "latch": latch,
            "mode": mode,
            "inverted": inverted,
        }


class Pinbot:
    """
    Board class representing the Pinbot hardware platform.

    Contains two TCA9535 I/O expanders:
    - io1 (default address 0x20): General purpose outputs / peripherals
    - io2 (default address 0x21): Relays, USB Hub controls, alert inputs
    """

    def __init__(self, bus_number=1, address_io1=0x20, address_io2=0x21):
        self.io1 = TCA9535(i2c_address=address_io1, bus_number=bus_number)
        self.io2 = TCA9535(i2c_address=address_io2, bus_number=bus_number)
        self.relay = RelayControl(self)
        self.led = LedControl(self)
        self.usb = UsbControl(self)
        self.signal = SignalControl(self)

        # Hardware Interrupt Handling using lgpio (TCA2 (io2) INT is connected to GPIO 5)
        self.lgpio_handle = None
        self.lgpio_callback = None

        if LGPIO_AVAILABLE:
            try:
                # Open gpiochip 0
                self.lgpio_handle = lgpio.gpiochip_open(0)
                # Claim GPIO 5 (TCA2 INT) for falling-edge alert
                lgpio.gpio_claim_alert(self.lgpio_handle, 5, lgpio.FALLING_EDGE)
                # Register callback
                self.lgpio_callback = lgpio.callback(
                    self.lgpio_handle,
                    5,
                    lgpio.FALLING_EDGE,
                    self._handle_interrupt
                )
                logging.info("Hardware interrupt monitoring enabled on GPIO 5")
            except Exception as e:
                logging.warning(f"Could not initialize lgpio hardware interrupts: {e}")

    def _handle_interrupt(self, chip, gpio, level, timestamp):
        """
        Asynchronously handles the TCA2 (io2) interrupt pin falling edge.
        Reads the input port of io2 and automatically disables any faulted USB ports.
        """
        # Active low: level == 0 is falling edge
        if level != 0:
            return

        try:
            # Read Port 1 from U3 (io2)
            port1_val = self.io2.read_port(1)
            # USB_FLT1-4 are on pins 0-3 of Port 1
            for i in range(4):
                flt_pin = i
                # Active-low: 0 means fault
                if ((port1_val >> flt_pin) & 1) == 0:
                    port_id = i + 1
                    # Unconditionally disable the faulted port.
                    # The shadow cache may be stale if another process enabled
                    # the port, so we don't check whether we think it's enabled.
                    # Writing HIGH to an already-disabled port is harmless.
                    logging.error(f"Asynchronous fault detected on USB port {port_id}! Disabling port immediately.")
                    self.usb.disable(port_id)
                    self.usb.fault_occurred[port_id] = True
        except Exception as e:
            logging.error(f"Error handling USB fault interrupt: {e}")

    def init_default(self):
        """
        Configure the TCA9535 expanders on the board with the default settings
        exactly as in v2tca-test.py, using a safe initialization sequence
        to prevent glitches on outputs.
        """
        # Configure 1st TCA9535 (io1, address 0x20)
        # 1. Output latch values (all low)
        self.io1.write_port(0, 0x00)
        self.io1.write_port(1, 0x00)
        # 2. Polarities (all normal)
        self.io1.set_port_polarity(0, 0x00)
        self.io1.set_port_polarity(1, 0x00)
        # 3. Directions (all outputs)
        self.io1.set_port_direction(0, 0x00)
        self.io1.set_port_direction(1, 0x00)

        # Configure 2nd TCA9535 (io2, address 0x21)
        # 1. Output latch values (Port 0: all low, Port 1: USB disabled/high)
        self.io2.write_port(0, 0x00)
        self.io2.write_port(1, 0b11110000)
        # 2. Polarities:
        #   - Port 0: normal,
        #   - Port 1: SHOULD BE inverted (0xFF) for active-low MIC2026 signals,
        #       but confuse massively to debug, so preserve as normal at a moment
        self.io2.set_port_polarity(0, 0x00)
        self.io2.set_port_polarity(1, 0x00)
        # 3. Directions:
        # Port 0: P0.4, P0.5 are inputs (ADS1015 ALERTS), others are outputs
        self.io2.set_port_direction(0, 0b00110000)
        # Port 1: P1.0-P1.3 are inputs (USB_FLT), P1.4-P1.7 are outputs (USB_EN)
        self.io2.set_port_direction(1, 0b00001111)

    def close(self):
        """
        Close both TCA9535 I/O expander connections and release lgpio resources.
        """
        if self.lgpio_callback:
            try:
                self.lgpio_callback.cancel()
            except Exception:
                pass
        if self.lgpio_handle:
            try:
                lgpio.gpiochip_close(self.lgpio_handle)
            except Exception:
                pass
        self.io1.close()
        self.io2.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def init_default(bus_number=1, address_io1=0x20, address_io2=0x21):
    """
    Initialize and return a Pinbot board instance with default settings.
    """
    board = Pinbot(bus_number=bus_number, address_io1=address_io1, address_io2=address_io2)
    board.init_default()
    return board
