#coding: utf8

from ..service_proxy import ServiceProxy

import numpy as np

class ShuttersProxy(ServiceProxy):
    def __init__(self, *args, **kwargs):
        super(ShuttersProxy, self).__init__(*args, **kwargs)
        self.actuator_names = self.config["actuators"]
        self.nshutters = len(self.actuator_names)
        self.actuator_services = []
        for k in range(self.nshutters):
            self.actuator_services.append(self._testbed.get_service(self.actuator_names[k]))
        return None
    
    def set_position(self, states, actuator_indices = None):
        """
        Set the shutters to open or close
        param states: the states of the shutters (1 for open, 0 for close)
        param (optional) actuator_indices: a list of indices of the actuator to move, i.e actuator actuator_indices[k] will move to state states[k]
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
        return None