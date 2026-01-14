#coding: utf8

from ..service_proxy import ServiceProxy

import numpy as np
import time

class ShuttersProxy(ServiceProxy):
    def __init__(self, *args, **kwargs):
        super(ShuttersProxy, self).__init__(*args, **kwargs)
        self.actuator_names = self.config["actuators"]
        self.nshutters = len(self.actuator_names)
        self.actuator_services = []
        for k in range(self.nshutters):
            self.actuator_services.append(self._testbed.get_service(self.actuator_names[k]))
        return None

    def get_states(self, actuator_indices = None):
        """
        Return the state of the shutters (1 for open, 0 for close, -1 for unknown)
        param (optional) actuator_indices: a list of indices of the actuator to check
        """      
        if actuator_indices is None:
            actuator_indices = list(range(self.nshutters))  
        states = []      
        for k in range(len(actuator_indices)):
            position = self.actuator_services[actuator_indices[k]].current_position_stream.get()[0]
            if position == 0.0:
                state = 0
            elif position == 31.0:
                state = 1
            else:
                state = -1
            states.append(state) 
        return states

    def set_states(self, states, actuator_indices = None, wait = True, timeout = 10):
        """
        Set the shutters to open or close
        param states: the states of the shutters (1 for open, 0 for close)
        param (optional) actuator_indices: a list of indices of the actuator to move, i.e actuator actuator_indices[k] will move to state states[k]
        param (optional) wait: wait until shutters have reached the requested state. If False, returns immediately
        """        
        # if no indices are given, assume that the users wants to move everything
        if actuator_indices is None:
            actuator_indices = list(range(self.nshutters))
        if len(states) != len(actuator_indices):
            raise Exception("The number of positions should match the number of delay lines to move")
        for k in range(len(actuator_indices)):
            if states[k] == 0:
                position = 0.0
            elif states[k] == 1:
                position = 31.0
            else:
                ValueError("Shutter state can only be 0 or 1")
            self.actuator_services[actuator_indices[k]].position_stream.submit_data(np.array([position], "float64")) 
        t0 = time.time()
        if wait:
            done = False
            while not(done):
                if time.time() - t0 > timeout:
                    raise Exception("Timeout when setting shutter states!")
                current_states = self.get_states(actuator_indices=actuator_indices)
                done = True
                for k in range(len(actuator_indices)):
                    if states[k] != current_states[k]:
                        done = False
            time.sleep(0.1)
        return None