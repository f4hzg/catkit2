"""
The library calls for the Thorlabs elliptec in this script make use and adapt code from
https://github.com/Thorlabs/Motion_Control_Examples/tree/main/Python, which is licensed under the MIT License.
Their original copyright notice and permission notice are included below.

Copyright (c) 2021 Thorlabs

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from catkit2.testbed.service import Service

import sys, os, time
import clr
import numpy as np

# load methods for Thorlabs DLL
default_dll_path = os.environ.get('THORLABS_ELLIPTEC_DLL_PATH')
dll_name = "Thorlabs.Elliptec.ELLO_DLL.dll"
if default_dll_path is not None:
    if sys.version_info < (3, 8):
        os.chdir(default_dll_path)
    else:
        os.add_dll_directory(default_dll_path)
else:
    raise ValueError('To use Thorlabs cube motors with Kinesis, you need to set the THORLABS_KINESIS_DLL_PATH environment variable.')

clr.AddReference(default_dll_path + "/" + dll_name)

from Thorlabs.Elliptec.ELLO_DLL import *
import System

class ThorlabsElliptecBoard(Service):
    """
    Thorlabs Elliptec systems are connected to an interface board. This class represents this interface board. A number of potentially different
    elliptec systems can be connected to the interface board and will be represented ax Proxies talking to this central class. The role of this
    class is to centralize communication to the single USB port, and forward commands. Since different types of systems can be connected,
    the commands need to be interpreted differently.
    """
    _MAX_NUM_RETRIES = 3

    def __init__(self):
        super().__init__('thorlabs_elliptec_board')
        self.port = self.config['port']
        self.min_address = str(self.config["min_address"])
        self.max_address = str(self.config["max_address"])
        # data stream for all addresses:
        self.current_position_streams = {}
        self.position_streams = {}
        for k in range(int(self.min_address, 16), int(self.max_address, 16)+1):
            self.current_position_streams['{:x}'.format(k).upper()] = self.make_data_stream('current_position_{}'.format(k), 'float64', [1], 20)
            self.position_streams['{:x}'.format(k).upper()] = self.make_data_stream('position_{}'.format(k), 'float64', [1], 20)

    def open(self): 
        """
        Opens the USB port and connectt to the interface board. 
        """
        # Connect to device
        ELLDevicePort.Connect(self.port)
        ellDevices=ELLDevices()
        # scan all the addresses as request from config file, looking for the correct serial number
        # if the user know the address of the device, best to provide it in the config
        devices=ellDevices.ScanAddresses(self.min_address, self.max_address)
        # to initial device, we loop through all devices at the different addresses.
        # for each we want to store the elliptec device type and the serial number
        self.addressedDevices = {} 
        for device in devices:
            if ellDevices.Configure(device):
                addressedDevice=ellDevices.AddressedDevice(device[0])
                deviceInfo=addressedDevice.DeviceInfo
                deviceType=deviceInfo.DeviceType
                for stri in deviceInfo.Description():
                    if "Serial Number:" in stri:
                        serial_number = stri.split("Serial Number:")[1].strip()
                self.addressedDevices[addressedDevice.get_Address()] = {"handle": addressedDevice, "serial_number": serial_number, "device_type": deviceType}
                # Send home and submit starting position to current_position data stream
                self.init_device(addressedDevice.get_Address())

    def main(self):
        while not self.should_shut_down:
            for address in self.addressedDevices:
                handle, device_type = self.get_device(address)
                try:
                    target_position = self.position_streams[address].get()[0]
                except Exception:
                # Timed out. This is used to periodically check the shutdown flag.
                    continue
                # Try setting the position a few times before giving up.
                while not self.should_shut_down:
                    try:
                        self.set_position(address, target_position)
                        break
                    except Exception:
                        raise

    def close(self):
        ELLDevicePort.Disconnect()
        return None

    def get_device(self, address):
        """
        A convenience method to get the device handle and its type
        """
        if not(address in self.addressedDevices):
            raise ValueError("No known device at address {}.".format(address))
        return (self.addressedDevices[address]["handle"], self.addressedDevices[address]["device_type"])

    def init_device(self, address):
        """
        Initialize the device at the given address and its associated data frames
        """
        handle, device_type = self.get_device(address)
        if device_type in [DeviceID.DeviceTypes.Shutter]:
            handle.Home()
            self.get_current_position(address)
        return None

    def get_current_position(self, address):
        """
        returns the current position of the device at the given address. Depending on the type of device, the exact meaning and unit
        of this position can be different (i.e. an angle in deg for a rotation stage; a position in mm for slider, etc.)
        """
        handle, device_type = self.get_device(address)
        current_position = System.Decimal.ToDouble(handle.get_Position())
        self.current_position_streams[address].submit_data(np.array([current_position], dtype='float64'))

    def set_position(self, address, position):
        """
        move the device at the given address to the given absolute position. Depending on the type of device, the exact meaning and unit
        of this position can be different (i.e. an angle in deg for a rotation stage; a position in mm for slider, etc.)
        """
        handle, device_type = self.get_device(address)
        if (device_type in [DeviceID.DeviceTypes.Shutter, DeviceID.DeviceTypes.RotaryStage18]):
            try:
                if position == self.current_position_streams[address].get()[0]:
                    return
            except Exception:
                # No previous position known.
                pass
            handle.MoveAbsolute(System.Decimal(position))
            self.current_position_streams[address].submit_data(np.array([position], "float64"))        
        else:
            raise ValueError("Function not available for this type of device.")
        return None

if __name__ == '__main__':
    service = ThorlabsElliptecBoard()
    service.run()
