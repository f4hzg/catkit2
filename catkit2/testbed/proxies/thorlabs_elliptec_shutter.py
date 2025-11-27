#coding: utf8
import numpy as np
from enum import Enum

from ..service_proxy import ServiceProxy

import time
import numpy as np

class ThorlabsElliptecShutterProxy(ServiceProxy):

    def __init__(self, *args, **kwargs):
        super(ThorlabsElliptecShutterProxy, self).__init__(*args, **kwargs)
        self.board_service_name = self.config["board_service"]
        self.address = self.config["address"] 
        self.board_service = self.testbed.get_service(self.board_service_name)
        self.position_stream = self.board_service.get_data_stream("position_{}".format(self.address))
        self.current_position_stream = self.board_service.get_data_stream("current_position_{}".format(self.address))
        return None

    def get_position(self):
        """
        A convenience method which attempts to resolve the current position name based on the list given in the config file
        """
        position = self.current_position.get()[0]
        named_position = "Unknown"
        for key in self.config["positions"].keys():
            if self.config["positions"][key] == position:
                named_position = key
        return named_position

    def set_position(self, named_position):
        """
        A convenience method which attempts to resolve and set the given position name based on the list given in the config file
        """
        if named_position in self.config["positions"].keys():
            position = self.config["positions"][named_position]
        else:
            raise Exception("{} is not in the list of available positions.".format(named_position))
        self.position_stream.submit_data(np.array([position], "float64"))
        return None