#coding: utf8
import numpy as np
import time

from enum import Enum

from ..service_proxy import ServiceProxy

class Emission(Enum):
    off = 0
    on = 1

class Interlock(Enum):
    interlock_off = 0
    waiting_for_interlock_reset = 256
    interlock_ok = 512
    interlock_power_failure = 16
    internal_interlock = 32
    external_bus_interlock = 48
    door_interlock = 64
    key_switch = 80
    interlock_circuit_failure = 255    

class NktSuperkEvoProxy(ServiceProxy):
    @property
    def center_wavelength(self):
        return (self.swp_setpoint.get()[0] + self.lwp_setpoint.get()[0]) / 2

    @center_wavelength.setter
    def center_wavelength(self, center_wavelength):
        self.set_spectrum(center_wavelength=center_wavelength, wait=False)

    @property
    def bandwidth(self):
        return self.swp_setpoint.get()[0] - self.lwp_setpoint.get()[0]

    @bandwidth.setter
    def bandwidth(self, bandwidth):
        self.set_spectrum(bandwidth=bandwidth, wait=False)

    def set_spectrum(self, center_wavelength=None, bandwidth=None, wait=True):
        '''Set both center wavelength and bandwidth simultaneously.

        Parameters
        ----------
        center_wavelength : scalar, optional
            The new center wavelength of the tunable filter. If this is not given, the
            center wavelength will not be changed.
        bandwidth : scalar, optional
            The new bandwidth of the tunable filter. If this is not given, the bandwidth
            will not be changed.
        '''
        if center_wavelength is None:
            center_wavelength = self.center_wavelength

        if bandwidth is None:
            bandwidth = self.bandwidth

        # Raise an error if the bandwidth is negative for safety reasons.
        if bandwidth < 0:
            raise ValueError('Negative bandwidths are considered dangerous for the NKT VARIA.')

        lwp = center_wavelength - bandwidth / 2
        swp = center_wavelength + bandwidth / 2

        current_lwp = self.lwp_setpoint.get()[0]
        current_swp = self.swp_setpoint.get()[0]

        # Back out early if we do not need to move the VARIA filter.
        if np.allclose(lwp, current_lwp) and np.allclose(swp, current_swp):
            return

        sleep_time = max(abs(lwp - current_lwp), abs(swp - current_swp)) * self.sleep_time_per_nm

        self.lwp_setpoint.submit_data(np.array([lwp], dtype='float32'))
        self.swp_setpoint.submit_data(np.array([swp], dtype='float32'))

        if wait:
            time.sleep(self.base_sleep_time + sleep_time)

        self.base_temperature = self.make_data_stream('base_temperature', 'float32', [1], 20)
        self.supply_voltage = self.make_data_stream('supply_voltage', 'float32', [1], 20)
        self.external_control_input = self.make_data_stream('external_control_input', 'float32', [1], 20)
        self.interlock = self.make_data_stream('interlock', 'uint16', [1], 20)

        self.emission = self.make_data_stream('emission', 'uint8', [1], 20)
        self.power_setpoint = self.make_data_stream('power_setpoint', 'float32', [1], 20)
        self.current_setpoint = self.make_data_stream('current_setpoint', 'float32', [1], 20)

    # convenience methods
    def get_emission_status(self):
        emission = self.emission.get()
        return Emission(emission[0])

    def get_interlock_status(self):
        interlock = self.interlock.get()
        return Interlock(interlock[0])

    def get_status(self):
        status = {}
        status["emission"] = self.get_emission_status().name
        status["interlock"] = self.get_interlock_status().name
        status["power_setpoint"] = self.power_setpoint.get()[0]
        status["current_setpoint"] = self.current_setpoint.get()[0]        
        status["base_temperature"] = self.base_temperature.get()[0]
        status["supply_voltage"] = self.supply_voltage.get()[0]
        status["external_control_input"] = self.external_control_input.get()[0]
        return status

    def set_power(self, value):
        self.power_setpoint.submit_data(np.array([value], dtype="float32"))
        return self.power_setpoint.get()[0]

    def switch_emission(self, state):
        if state:
            # check the interlock before attempting to turn the source on
            interlock = self.get_interlock_status()
            if interlock != Interlock.interlock_ok:
                # to avoid incoherences between emisison and true state of the source, we set 
                # the emission back to 0
                self.emission.submit_data(np.array([0], "uint8"))
                raise Exception("Interlock status: {}".format(interlock.name))
            else:
                self.emission.submit_data(np.array([1], "uint8"))
        else:
            self.emission.submit_data(np.array([0], "uint8"))
        # return the emission status
        return self.get_emission_status()

    @property
    def sleep_time_per_nm(self):
        return self.config['sleep_time_per_nm']

    @property
    def base_sleep_time(self):
        return self.config['base_sleep_time']
