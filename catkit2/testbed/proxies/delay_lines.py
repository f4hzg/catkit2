#coding: utf8

from ..service_proxy import ServiceProxy

import numpy as np

class DelayLinesProxy(ServiceProxy):
    def __init__(self, *args, **kwargs):
        super(DelayLinesProxy, self).__init__(*args, **kwargs)
        self.actuator_names = self.config["actuators"]
        self.ndls = len(self.actuator_names)
        self.actuator_services = []
        for k in range(self.ndls):
            self.actuator_services.append(self._testbed.get_service(self.actuator_names[k]))
        return None
    
    def set_velocity(self, velocities, actuator_indices = None):
        """
        Set the ,ax velocity of the lines (in mm/s)
        param velocity: an array of float values giving the velocities for the actuators
        param (optional) actuator_indices: a list of indices of the actuator to move, i.e actuator actuator_indices[k] will move to target_position[k]
        """
        # if no indices are given, assume that the users wants to move everything
        if actuator_indices is None:
            actuator_indices = list(range(self.ndls))
        if len(velocities) != len(actuator_indices):
            raise Exception("The number of positions should match the number of delay lines to move")
        for k in range(len(actuator_indices)):
            datastream = self.actuator_services[actuator_indices[k]].velocity_parameters
            datastream.submit_data(np.array([velocities[k], 0.5], dtype='float64'))
        return None    
    
    def get_positions(self, actuator_indices = None):
        "Return the position of the actuators"
        if actuator_indices is None:
            actuator_indices = list(range(self.ndls))
        positions = []
        for k in range(len(actuator_indices)):
            pos = self.actuator_services[actuator_indices[k]].current_position.get()[0]
            positions.append(pos)
        return positions
    
    def move_absolute(self, target_positions, actuator_indices = None):
        """
        Move the delay lines to the given target positions
        param target_positions: an array of float values giving the absolute positions for the actuators
        param (optional) actuator_indices: a list of indices of the actuator to move, i.e actuator actuator_indices[k] will move to target_position[k]
        """
        # if no indices are given, assume that the users wants to move everything
        if actuator_indices is None:
            actuator_indices = list(range(self.ndls))
        if len(target_positions) != len(actuator_indices):
            raise Exception("The number of positions should match the number of delay lines to move")
        for k in range(len(actuator_indices)):
            self.actuator_services[actuator_indices[k]].move_absolute(target_positions[k])
        return None

    def move_relative(self, distances, actuator_indices = None):
        """
        Move the delay lines to the given target positions
        param distances: an array of float values giving the delta of positions for the actuators
        param (optional) actuator_indices: a list of indices of the actuator to move, i.e actuator actuator_indices[k] will move by distances[k]
        """        
        # if no indices are given, assume that the users wants to move everything
        if actuator_indices is None:
            actuator_indices = list(range(self.ndls))
        if len(distances) != len(actuator_indices):
            raise Exception("The number of positions should match the number of delay lines to move")
        for k in range(len(actuator_indices)):
            self.actuator_services[actuator_indices[k]].move_relative(distances[k])
        return None

    def set_position(self, named_position):
        """
        Move the delay lines to a set position as defined in the config yml
        """
        if not(named_position in self.config['positions']):
            ValueError("Position {} not defined in the configguration".format(named_position)) 
        positions = self.config["positions"][named_position]
        self.move_absolute(positions)
        return None

    def home(self, actuator_indices = None):
        """
        Home the actuators of the delay lines
        param (optional) actuator_indices: a list of indices of the actuator to home, i.e actuator actuator_indices[k] will move by distances[k]
        """    
        # if no indices are given, assume that the users wants to home everything
        if actuator_indices is None:
            actuator_indices = list(range(self.ndls))        
        for k in range(len(actuator_indices)):
            self.actuator_services[actuator_indices[k]].home()
