#coding: utf8
import numpy as np
from enum import Enum

from ..service_proxy import ServiceProxy

class ThorlabsFW102CProxy(ServiceProxy):
    # convenience methods
    def get_filter(self):
        """
        A convenience method which attempts to resolve the current filter name based on the list given in the config file
        """
        # attempt to resolve the filter
        position = self.current_position.get()[0]
        filt = "Unknown"
        for key in self.config["filters"].keys():
            if self.config["filters"][key] == position:
                filt = key
        return {filt: position}

    def set_filter(self, filt):
        """
        A convenience method which attempts to resolve and set the given filter name based on the list given in the config file
        """
        if type(filt) == str:
            # attempt to resolve the name
            if filt in self.config["filters"].keys():
                filt = self.config["filters"][filt]
            else:
                raise Exception("{} is not in the list of available filters.".format(filt))
        self.position.submit_data(np.array([filt], "int8"))
        return None