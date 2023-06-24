
#!/usr/bin/env python -u

import usb.core
import usb.backend
import struct
import sys


be = usb.backend.libusb1.get_backend(find_library=lambda x: "/opt/anaconda3/envs/wasatch3/lib/python3.7/site-packages/libusb/_platform/_osx/x64/libusb-1.0.dylib")
dev = usb.core.find(idVendor=0x24aa, idProduct=0x4000, backend = be)
if dev is None:
    print("No spectrometer found.")
    sys.exit()
else: print(dev)


HOST_TO_DEVICE = 0x40
DEVICE_TO_HOST = 0xC0
TIMEOUT_MS     = 5000

# read "active_pixels_horizontal" from EEPROM page 2 (64 bytes)
buf = dev.ctrl_transfer(DEVICE_TO_HOST, 0xff, 0x01, 2, 64, TIMEOUT_MS)
print(buf)
pixels = struct.unpack("h", buf[16:18])[0] # per ENG-0034
print("EEPROM page 2 active_pixels_horizontal: %d" % pixels)

# request a spectrum
dev.ctrl_transfer(HOST_TO_DEVICE, 0xad, 0, 0, [0] * 8, TIMEOUT_MS)

# read the spectrum
print("reading %d pixels" % pixels)
data = dev.read(0x82, pixels * 2) # uint16

# dump the spectrum
for i in range(0, len(data), 2):
    lsb = data[i]
    msb = data[i + 1]
    value = msb << 8 | lsb
#    print value
    
Data = dev.read(0x82, pixels)
print(data)