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

    def move_absolute(self, position):
        """
        Move the rotation stage to the requested position (in deg)
        """
        if (position >= 360) or (position <= -360):
            raise ValueError("position must be between -360 and 360 (exlucded)")
        self.position_stream.submit_data(np.array([position], "float64"))
        return None        