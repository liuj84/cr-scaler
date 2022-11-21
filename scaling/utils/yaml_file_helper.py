""" helper functions for yaml file which is used for values
"""
import copy
import logging
from datetime import datetime
import yaml
from .constants import Constants
logger = logging.getLogger(Constants.LOGGER)

class YamlFileHelper(object):
    """ helper functions for yaml file which is used for values
    """

    @staticmethod
    def load_values(filename):
        """ load current values file
        Args:
            filename (str): values filename used for installing this cluster            
        Returns:
            dict 
        Raises: yaml.YAMLError
        """
        try:
            values = None
            with open(filename) as file:
                values = yaml.safe_load(file)
            return values
        except yaml.YAMLError as ex:
            logger.error("yaml error: {}".format(ex))
            raise


    @staticmethod
    def write_values(filename, values):
        """ update values with new values and write to given file 
        Args:
            filename (str): output filename          
            values (dict): values dictionary returned from loading values file
        Returns:
        Raises: yaml.YAMLError
        """
        try:
            with open(filename, 'w') as outfile:
                # dump with default_flow_style=False, which emits output in block style
                outfile.write(yaml.safe_dump(values, default_flow_style=False))
                outfile.flush()
                outfile.close()
            logger.debug("Wrote updated values to {}".format(filename))
        except yaml.YAMLError as ex:
            print(ex)
            logger.error("yaml error: {}".format(ex))
            raise


    def deepupdate(self, target, src):
        """Deep update target dict with src
        For each k,v in src: if k doesn't exist in target, it is deep copied from
        src to target. Otherwise, if v is a list, target[k] is extended with
        src[k]. If v is a set, target[k] is updated with v, If v is a dict,
        recursively deep-update it.

        Examples:
        >>> t = {'name': 'Ferry', 'hobbies': ['programming', 'sci-fi']}
        >>> deepupdate(t, {'hobbies': ['gaming']})
        >>> print t
        {'name': 'Ferry', 'hobbies': ['programming', 'sci-fi', 'gaming']}
        """
        for k, v in src.items():
            if type(v) == list:
                if not k in target:
                    target[k] = copy.deepcopy(v)
                else:
                    target[k].extend(v)
            elif type(v) == dict:
                if not k in target:
                    target[k] = copy.deepcopy(v)
                else:
                    self.deepupdate(target[k], v)
            elif type(v) == set:
                if not k in target:
                    target[k] = v.copy()
                else:
                    target[k].update(v.copy())
            else:
                target[k] = copy.copy(v)


    @staticmethod
    def merge(data, base):
        """
        Merges a dict of data into an existing base, taking the data as source-of-truth if duplicate fields exists.
        """
        if isinstance(data, dict) and isinstance(base, dict):
            for k, v in base.items():
                if k not in data:
                    data[k] = v
                else:
                    data[k] = YamlFileHelper.merge(data[k], v)
        return data


    @staticmethod
    def load_multiple_values(file_list, debug=False):
        global values
        """
        Iterates over values files to create one source-of-truth.
        Args:
            file_list (str,str,..): comma separated file list
        Returns:
            dict: dictionary of values loaded and merged from the given file list
        """
        paths = file_list.split(',')
        try:
            values = None
            for i in range(len(paths)):
                logger.debug("Loading values: " + paths[i])
                with open(paths[i]) as f:
                    data = yaml.safe_load(f)
                    values = YamlFileHelper.merge(data, values)
            if debug:
                logger.debug("Merged values:")
                logger.debug(yaml.safe_dump(values, default_flow_style=False))

            return values
        except yaml.YAMLError as ex:
            logger.error("yaml error: {}".format(ex))
            raise
