#coding: utf8
import numpy as np
from enum import Enum

from ..service_proxy import ServiceProxy

import time
import numpy as np

class ThorlabsElliptecRotationStageProxy(ServiceProxy):

    def __init__(self, *args, **kwargs):
        super(ThorlabsElliptecRotationStageProxy, self).__init__(*args, **kwargs)
        self.board_service_name = self.config["board_service"]
        self.address = self.config["address"] 
        self.board_service = self.testbed.get_service(self.board_service_name)
        self.position_stream = self.board_service.get_data_stream("position_{}".format(self.address))
        self.current_position_stream = self.board_service.get_data_stream("current_position_{}".format(self.address))
        return None

    def get_position(self):
        """
        Return the current position of the rotation stage (in deg)
        """
        position = self.current_position.get()[0]
        return position        

    def set_named_position(self, named_position):
        """
        A convenience method which attempts to resolve and set the given position name based on the list given in the config file
        """
        if named_position in self.config["positions"].keys():
            position = self.config["positions"][named_position]
        else:
            raise Exception("{} is not in the list of available positions.".format(named_position))
        self.move_absolute(position)
        return None

    def move_absolute(self, position):
        """
        Move the rotation stage to the requested position (in deg)
        """
        if (position >= 360) or (position <= -360):
            raise ValueError("position must be between -360 and 360 (exlucded)")
        self.position_stream.submit_data(np.array([position], "float64"))
        return None        