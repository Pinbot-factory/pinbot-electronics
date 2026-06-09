import logging
import threading

import smbus2 as smbus


# TCA9535 registers config
# ============================================================================

INPUT_PORT_0 = 0x00
INPUT_PORT_1 = 0x01

OUTPUT_PORT_0 = 0x02
OUTPUT_PORT_1 = 0x03

POLARITY_PORT_0 = 0x04
POLARITY_PORT_1 = 0x05

CONFIG_PORT_0 = 0x06
CONFIG_PORT_1 = 0x07


# Constants
# ============================================================================

INPUT = 1
OUTPUT = 0

LOW = 0
HIGH = 1

DEFAULT_ADDRESS = 0x20


# TCA9535
# ============================================================================

class TCA9535:
    """
    TCA9535 16-bit I2C GPIO expander driver.

    Features:
    - Per-pin direction control
    - Per-pin read/write
    - Port read/write
    - Shadow register cache
    - Thread-safe access
    - Polarity inversion
    - Safe initialization
    """

    def __init__(
        self,
        i2c_address=DEFAULT_ADDRESS,
        bus_number=1,
    ):

        self.address = i2c_address
        self.bus = smbus.SMBus(bus_number)
        self.lock = threading.Lock()

        # --------------------------------------------------------------------
        # Read current register state to fill shadow cache
        # --------------------------------------------------------------------

        with self.lock:
            # 1. Read CONFIG
            config_port_0 = self._read_register(CONFIG_PORT_0)
            config_port_1 = self._read_register(CONFIG_PORT_1)
            self.config = [
                config_port_0 & 0xFF,
                config_port_1 & 0xFF,
            ]

            # 2. Read OUTPUT
            output_port_0 = self._read_register(OUTPUT_PORT_0)
            output_port_1 = self._read_register(OUTPUT_PORT_1)
            self.output = [
                output_port_0 & 0xFF,
                output_port_1 & 0xFF,
            ]

            # 3. Read POLARITY
            polarity_port_0 = self._read_register(POLARITY_PORT_0)
            polarity_port_1 = self._read_register(POLARITY_PORT_1)
            self.polarity = [
                polarity_port_0 & 0xFF,
                polarity_port_1 & 0xFF,
            ]

        logging.debug(
            f"TCA9535 initialized at 0x{self.address:02X} by reading physical registers"
        )

    # =========================================================================
    # Low-level I2C
    # =========================================================================

    def _write_register(self, register, value):
        self.bus.write_byte_data(
            self.address,
            register,
            value & 0xFF
        )

    def _read_register(self, register):
        return self.bus.read_byte_data(
            self.address,
            register
        )

    # =========================================================================
    # Validation
    # =========================================================================

    @staticmethod
    def _validate_port(port):
        if port not in (0, 1):
            raise ValueError("Port must be 0 or 1")

    @staticmethod
    def _validate_pin(pin):
        if not 0 <= pin <= 7:
            raise ValueError("Pin must be in range 0-7")

    @staticmethod
    def _validate_mode(mode):
        if mode not in (INPUT, OUTPUT):
            raise ValueError("Mode must be INPUT or OUTPUT")

    @staticmethod
    def _validate_state(state):
        if state not in (LOW, HIGH):
            raise ValueError("State must be LOW or HIGH")

    # =========================================================================
    # Direction control
    # =========================================================================

    def pin_mode(self, port, pin, mode):
        """
        Set pin direction.

        INPUT  = 1
        OUTPUT = 0
        """

        self._validate_port(port)
        self._validate_pin(pin)
        self._validate_mode(mode)

        with self.lock:

            if mode == INPUT:
                self.config[port] |= (1 << pin)
            else:
                self.config[port] &= ~(1 << pin)

            register = (
                CONFIG_PORT_0
                if port == 0
                else CONFIG_PORT_1
            )

            self._write_register(register, self.config[port])

    def set_port_direction(self, port, direction_mask):
        """
        Configure entire port.

        Bit:
            1 = INPUT
            0 = OUTPUT
        """

        self._validate_port(port)

        with self.lock:

            self.config[port] = direction_mask & 0xFF

            register = (
                CONFIG_PORT_0
                if port == 0
                else CONFIG_PORT_1
            )

            self._write_register(register, self.config[port])

    # =========================================================================
    # Digital write
    # =========================================================================

    def digital_write(self, port, pin, state):
        """
        Write pin state.

        Uses shadow registers to avoid read-modify-write races.
        """

        self._validate_port(port)
        self._validate_pin(pin)
        self._validate_state(state)

        with self.lock:

            if state == HIGH:
                self.output[port] |= (1 << pin)
            else:
                self.output[port] &= ~(1 << pin)

            register = (
                OUTPUT_PORT_0
                if port == 0
                else OUTPUT_PORT_1
            )

            self._write_register(register, self.output[port])

    def write_port(self, port, value):
        """
        Write entire 8-bit port.
        """

        self._validate_port(port)

        with self.lock:

            self.output[port] = value & 0xFF

            register = (
                OUTPUT_PORT_0
                if port == 0
                else OUTPUT_PORT_1
            )

            self._write_register(register, self.output[port])

    # =========================================================================
    # Digital read
    # =========================================================================

    def digital_read(self, port, pin):
        """
        Read physical pin state.
        """

        self._validate_port(port)
        self._validate_pin(pin)

        register = (
            INPUT_PORT_0
            if port == 0
            else INPUT_PORT_1
        )

        value = self._read_register(register)

        return HIGH if (value & (1 << pin)) else LOW

    def read_port(self, port):
        """
        Read physical 8-bit port state.
        """

        self._validate_port(port)

        register = (
            INPUT_PORT_0
            if port == 0
            else INPUT_PORT_1
        )

        return self._read_register(register)

    # =========================================================================
    # Output latch access
    # =========================================================================

    def get_output_port(self, port):
        """
        Return cached output latch state.
        """

        self._validate_port(port)

        return self.output[port]

    # =========================================================================
    # Polarity inversion
    # =========================================================================

    def set_polarity_inversion(self, port, pin, enabled):
        """
        Invert input polarity for a pin.
        """

        self._validate_port(port)
        self._validate_pin(pin)

        with self.lock:

            if enabled:
                self.polarity[port] |= (1 << pin)
            else:
                self.polarity[port] &= ~(1 << pin)

            register = (
                POLARITY_PORT_0
                if port == 0
                else POLARITY_PORT_1
            )

            self._write_register(register, self.polarity[port])

    def set_port_polarity(self, port, polarity_mask):
        """
        Configure entire polarity inversion port.

        Bit:
            1 = Inverted
            0 = Normal
        """

        self._validate_port(port)

        with self.lock:

            self.polarity[port] = polarity_mask & 0xFF

            register = (
                POLARITY_PORT_0
                if port == 0
                else POLARITY_PORT_1
            )

            self._write_register(register, self.polarity[port])

    # =========================================================================
    # Utilities
    # =========================================================================

    def dump_registers(self):
        """
        Return current device register snapshot.
        """

        return {
            "input_port_0": self._read_register(INPUT_PORT_0),
            "input_port_1": self._read_register(INPUT_PORT_1),

            "output_port_0": self._read_register(OUTPUT_PORT_0),
            "output_port_1": self._read_register(OUTPUT_PORT_1),

            "polarity_port_0": self._read_register(POLARITY_PORT_0),
            "polarity_port_1": self._read_register(POLARITY_PORT_1),

            "config_port_0": self._read_register(CONFIG_PORT_0),
            "config_port_1": self._read_register(CONFIG_PORT_1),
        }

    # =========================================================================
    # Cleanup
    # =========================================================================

    def close(self):
        self.bus.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
