"""
Debug helper to monitor Pinbot's IO expanders
in (kinda) real time.
https://github.com/Pinbot-factory
"""
import time
import smbus2 as smbus

CHIPS = {
    "0x20": 0x20,
    "0x21": 0x21,
}

# Registers
INPUT_PORT_0 = 0x00
INPUT_PORT_1 = 0x01
OUTPUT_PORT_0 = 0x02
OUTPUT_PORT_1 = 0x03
POLARITY_PORT_0 = 0x04
POLARITY_PORT_1 = 0x05
CONFIG_PORT_0 = 0x06
CONFIG_PORT_1 = 0x07

bus = smbus.SMBus(1)

# Terminal symbols
RED = "\033[91m"
GRAY = "\033[90m"
YELLOW = "\033[93m"
RESET = "\033[0m"

# Signal map
SIGNALS = {
    (0x20, 0, 0): "GPIO0",
    (0x20, 0, 1): "GPIO1",
    (0x20, 0, 2): "GPIO2",
    (0x20, 0, 3): "GPIO3",
    (0x20, 0, 4): "GPIO4",
    (0x20, 0, 5): "GPIO5",
    (0x20, 0, 6): "GPIO6",
    (0x20, 0, 7): "GPIO7",

    (0x20, 1, 0): "GPIO8",
    (0x20, 1, 1): "GPIO9",
    (0x20, 1, 2): "GPIO10",
    (0x20, 1, 3): "GPIO11",
    (0x20, 1, 4): "GPIO12",
    (0x20, 1, 5): "GPIO13",
    (0x20, 1, 6): "GPIO14",
    (0x20, 1, 7): "GPIO15",

    (0x21, 0, 0): "RELAY1",
    (0x21, 0, 1): "RELAY2",
    (0x21, 0, 2): "RELAY3",
    (0x21, 0, 3): "RELAY4",
    (0x21, 0, 4): "ALERT0",
    (0x21, 0, 5): "ALERT1",
    (0x21, 0, 6): "USR_R",
    (0x21, 0, 7): "USR_G",

    (0x21, 1, 0): "USB_FLT1",
    (0x21, 1, 1): "USB_FLT2",
    (0x21, 1, 2): "USB_FLT3",
    (0x21, 1, 3): "USB_FLT4",
    (0x21, 1, 4): "USB_EN1",
    (0x21, 1, 5): "USB_EN2",
    (0x21, 1, 6): "USB_EN3",
    (0x21, 1, 7): "USB_EN4",
}

ACTIVE_LOW = {
    "USB_FLT1", "USB_FLT2", "USB_FLT3", "USB_FLT4",
    "USB_EN1", "USB_EN2", "USB_EN3", "USB_EN4"
}


def read(addr):
    return {
        "in": (
            bus.read_byte_data(addr, INPUT_PORT_0),
            bus.read_byte_data(addr, INPUT_PORT_1),
        ),
        "out": (
            bus.read_byte_data(addr, OUTPUT_PORT_0),
            bus.read_byte_data(addr, OUTPUT_PORT_1),
        ),
        "pol": (
            bus.read_byte_data(addr, POLARITY_PORT_0),
            bus.read_byte_data(addr, POLARITY_PORT_1),
        ),
        "cfg": (
            bus.read_byte_data(addr, CONFIG_PORT_0),
            bus.read_byte_data(addr, CONFIG_PORT_1),
        ),
    }


def get_bit(v, i):
    return (v >> i) & 1


def bit_string(v):
    return " ".join(str((v >> i) & 1) for i in range(7, -1, -1))


def semantic_state(raw, name):
    """
    Converts physical signal into logical meaning.
    Active-low signals are inverted here.
    """
    if name in ACTIVE_LOW:
        return 0 if raw else 1
    return raw

def sym(v):
    return f"{RED}●{RESET}" if v else f"{GRAY}○{RESET}"


NAME_W = 9


def build_col(addr, port, inp, cfg, offset):
    col = []

    for i in range(4):
        pin = offset + i
        name = SIGNALS.get((addr, port, pin), f"P{port}:{pin}")

        raw = get_bit(inp, pin)
        mode = get_bit(cfg, pin)

        state = semantic_state(raw, name)
        arrow = "←" if mode else "→"

        if name in ACTIVE_LOW:
            col.append(f"{pin} *{name:<{NAME_W}} {sym(state)} {arrow}")
        else:
            col.append(f"{pin} {name:<{NAME_W+1}} {sym(state)} {arrow}")

    return col


# UI LOOP
print("\033[2J", end="")

try:
    while True:
        print("\033[H\033[J", end="")

        for chip_name, addr in CHIPS.items():
            r = read(addr)

            print(f"{YELLOW}TCA9535 @ {chip_name}{RESET}")

            for port in (0, 1):

                inp = r["in"][port]
                out = r["out"][port]
                cfg = r["cfg"][port]
                pol = r["pol"][port]

                col_l = build_col(addr, port, inp, cfg, 0)
                col_r = build_col(addr, port, inp, cfg, 4)

                print(f"Port {port} │ 7 6 5 4 3 2 1 0       ┌──── Bits 0..3 ───┬──── Bits 4..7 ───┐")
                print(f"───────┼──────────────────     │ {col_l[0]:<26}│ {col_r[0]} │")
                print(f"State  │ {bit_string(inp)}       │ {col_l[1]:<26}│ {col_r[1]} │")
                print(f"Latch  │ {bit_string(out)}       │ {col_l[2]:<26}│ {col_r[2]} │")
                print(f"I/O    │ {' '.join('I' if (cfg >> i) & 1 else 'O' for i in range(7, -1, -1))}       │ {col_l[3]:<26}│ {col_r[3]} │")
                print(f"Inv?   │ {' '.join(f'{RED}Y{RESET}' if (pol >> i) & 1 else ' ' for i in range(7, -1, -1))}       └──────────────────┴──────────────────┘")
                print()

        print(f"* - active-low pins, ←/→ - pin in input/output mode, {RED}Y{RESET} - yes, pin inverted, {GRAY}○{RESET}/{RED}●{RESET} - pin inactive/active")
        print()
        print("Press Ctrl+C to exit")
        time.sleep(0.5)

except KeyboardInterrupt:
    print("\nStopped")