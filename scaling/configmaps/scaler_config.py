""" query k8s configmap and secret
"""
import logging
import json, os
from scaling.resources.manage_config import ManageConfig
from scaling.utils.yaml_file_helper import YamlFileHelper
from scaling.configmaps.scaling_configmap import ScalingConfigmap
from scaling.utils.constants import Constants

logger = logging.getLogger(Constants.LOGGER)

class ScalerConfigConfigmap(ScalingConfigmap):

    YAML_FILE_NAME = "config/scaler.yaml"

    def __init__(self):       
        self.CM_NAME = "scaling-config"
        self.CM_NAMESPACE = os.environ.get('POD_NAMESPACE')
        name = os.environ.get('RELEASE')
        if name is not None:
            self.CM_NAME = name +"-scaling-config"
            label = 'release'
            label_value = name
            self.LABELS = {label: label_value, "component": "cr-scaler"}
        else:
            self.LABELS = {"component": "cr-scaler"}
        self.label_selector = "{}={}".format("component", "cr-scaler")
        self.create()
        
    def create(self):
        if ManageConfig.exist_configmap(self.CM_NAMESPACE, self.CM_NAME):
            return
        print("create config map " + self.CM_NAME)
        values = YamlFileHelper.load_values(self.YAML_FILE_NAME)
        cm_data = dict()
        cm_data['data'] = json.dumps(values, indent=2)
        return ManageConfig.create_configmap(self.CM_NAMESPACE, self.CM_NAME, cm_data, self.LABELS, generate=False)

    def get(self):
        """get scaler config configmap
        Args:
        Returns: V1ConfigMap
        Raises: ApiException
        """
        configmap = ManageConfig.get_configmap(self.CM_NAMESPACE, self.CM_NAME)
        return configmap