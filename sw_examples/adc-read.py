"""
Analog read example for Pinbot used Chandra Wijaya lib ADS1x15
https://github.com/chandrawi/ADS1x15-ADC

Connect 1 potmeter

GND ---[   x   ]------ 3.3V
           |

measure at x (connect to any of AN0 AN1, AN2, AN3).
"""

import os
import time
import ADS1x15

# choose your sensor
# ADS = ADS1x15.ADS1013(1, 0x48)
# ADS = ADS1x15.ADS1014(1, 0x48)
ADS = ADS1x15.ADS1015(1, 0x44)
# ADS = ADS1x15.ADS1113(1, 0x48)
# ADS = ADS1x15.ADS1114(1, 0x48)

print(os.path.basename(__file__))
print("ADS1X15_LIB_VERSION: {}".format(ADS1x15.__version__))

# set gain to 4.096V max
# ADS.setGain(ADS.PGA_6_144V)
# ADS.setGain(ADS.PGA_4_096V)
ADS.setGain(ADS.PGA_2_048V)
# ADS.setGain(ADS.PGA_1_024V)
# ADS.setGain(ADS.PGA_0_512V)
# ADS.setGain(ADS.PGA_0_256V)

# multiply result based on divider (see Pinbot board schematic)
f = ADS.toVoltage() * 12

# clean screen one time
print("\033[2J", end="")

while True :
    # move cursor to the top left
    print("\033[H\033[1A", end="")

    val_0 = ADS.readADC(0)
    val_1 = ADS.readADC(1)
    val_2 = ADS.readADC(2)
    val_3 = ADS.readADC(3)
    print("Analog0: {0:d}\t{1:.3f} V".format(val_0, val_0 * f))
    print("Analog1: {0:d}\t{1:.3f} V".format(val_1, val_1 * f))
    print("Analog2: {0:d}\t{1:.3f} V".format(val_2, val_2 * f))
    print("Analog3: {0:d}\t{1:.3f} V".format(val_3, val_3 * f))
    print()
    #print(ADS.getMaxVoltage())
    #print(ADS._config)
    print("Press Ctrl+C to exit")
    time.sleep(0.1)
