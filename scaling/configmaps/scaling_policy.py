""" query k8s configmap and secret
"""
from datetime import datetime
import logging
from signal import siginterrupt
import sys
import os
import json

from scaling.configs.workloads import Workloads
sys.path.append(os.getcwd())
from scaling.resources.manage_config import ManageConfig
from scaling.configmaps.scaling_configmap import ScalingConfigmap
from scaling.utils.yaml_file_helper import YamlFileHelper
from scaling.utils.constants import Constants
from kubernetes.client.rest import ApiException

logger = logging.getLogger(Constants.LOGGER)

class ScalingPolicyConfigmap(ScalingConfigmap):

    CM_NAMESPACE = ""
    
    scaling_histsize = 10
    YAML_FILE_NAME = "config/scaling_policy.yaml"

    def __init__(self, ns, name, scaling_histsize):   
        self.CM_NAMESPACE = os.environ.get('POD_NAMESPACE')    
        name = os.environ.get('RELEASE')
        self.CM_NAME = "scaling-policy"
        if name is not None:
            self.CM_NAME = name +"-scaling-policy"
            label = 'release'
            label_value = name
            self.LABELS = {label: label_value, "component": "cr-scaler"}
        else:
            self.LABELS = {"component": "cr-scaler"}
        self.label_selector = "{}={}".format("component", "cr-scaler")
        self.scaling_histsize = scaling_histsize
        values = YamlFileHelper.load_values(self.YAML_FILE_NAME)
        self.cm_data_from_yaml = values['data']
        self.create()

    def create(self):
        if ManageConfig.exist_configmap(self.CM_NAMESPACE, self.CM_NAME):
            return
        logger.info("create config map " + self.CM_NAME)
        return ManageConfig.create_configmap(self.CM_NAMESPACE, self.CM_NAME, self.cm_data_from_yaml, self.LABELS, generate=False)

    def update_replicas(self, initial_replicas):
        policy = self.get().data
        patch = dict()
        patch["data"] = dict() 
        for type in policy:
            if type != "node":
                self.update_worker(patch["data"], policy, initial_replicas, type)
        logger.info("patch scaling-policy: {}".format(patch))
        self.patch(patch)

    def update_worker(self, patch_data, policy, initial_replicas, type):
        self.update_restriction_and_condition(patch_data, policy, type)
        self.update_pod_replicas(patch_data, policy, initial_replicas, type)

    def update_pod_replicas(self, patch_data, policy, initial_replicas, type):
        policy_data = json.loads(policy[type])
        # first time, update initalReplicas
        if "initialReplicas" not in policy_data:
            policy_data["initialReplicas"] = int(initial_replicas[type])
        policy_data["minReplicas"] = int(policy_data["initialReplicas"]) * policy_data["minScaleFactor"]
        policy_data["maxReplicas"] = int(policy_data["initialReplicas"]) * policy_data["maxScaleFactor"]
        patch_data[type] = json.dumps(policy_data, indent=2)
        policy[type] = json.dumps(policy_data, indent=2)

    def update_restriction_and_condition(self, patch_data, policy, type):
        policy_data = json.loads(policy[type])
        if type not in self.cm_data_from_yaml:
            return
        cm_policy = json.loads(self.cm_data_from_yaml[type])
        updated = False
        if "restrict" not in policy_data and "restrict" in cm_policy:
            policy_data["restrict"] = cm_policy["restrict"]
            updated = True
        if "scaleDownEnabled" not in policy_data and "scaleDownEnabled" in cm_policy:
            policy_data["scaleDownEnabled"] = cm_policy["scaleDownEnabled"]
            updated = True
        if "scaleUpEnabled" not in policy_data and "scaleUpEnabled" in cm_policy:
            policy_data["scaleUpEnabled"] = cm_policy["scaleUpEnabled"]
            updated = True
        if updated:
            patch_data[type] = json.dumps(policy_data, indent=2)
            policy[type] = json.dumps(policy_data, indent=2)

    def clone(self):
        """
        Create clone of this configmap with CM_NAME_PREFIX and k8s generated suffix
        This will be used for scaling history
        """
        return ManageConfig.copy_configmap(self.CM_NAMESPACE, self.CM_NAME, self.CM_NAME_PREFIX, self.LABELS, generate=True)


    def get(self):
        """get scaling configmap
        Args:
        Returns: V1ConfigMap
        Raises: ApiException
        """
        configmap = ManageConfig.get_configmap(self.CM_NAMESPACE, self.CM_NAME)
        return configmap


    def list(self):
        """get scaling configmap
        Args:
        Returns: V1ConfigMapList
        Raises: ApiException
        """
        configmaps = ManageConfig.list_configmap(self.CM_NAMESPACE, self.label_selector)
        return configmaps

    def sorted_list(self, reverse=True):
        """get scaling configmap
        Args:
        Returns: list[V1ConfigMap]
        Raises: ApiException
        """
        configmaps = ManageConfig.list_configmap(self.CM_NAMESPACE, self.label_selector)
        if configmaps:
            cm_list = configmaps.items  
            #cm_list.sort(key=lambda x: x.metadata.creation_timestamp, reverse=True)
            cm_list.sort(key=lambda x: x.metadata.resource_version)
            logger.info("sorted list: {}".format(cm_list))
            return cm_list
        return []
    

    def patch(self, body):
        """patch scaling configmap
        Args: 
        Returns: V1Status
        Raises: ApiException
        """
        return ManageConfig.patch_configmap(self.CM_NAMESPACE, self.CM_NAME, body)


    def delete(self):
        """delete scaling configmap
        clones configmap before deleting
        Args:
        Returns: V1Status
        Raises: ApiException
        """
        try:
            self.clone()
        except ApiException as ex:
            if ex.status != 404:
                raise
        
        try:
            # if scaling history size is greater than scaling_histsize, delete oldest entry
            configmaps = ManageConfig.list_configmap(self.CM_NAMESPACE, self.label_selector)
            if configmaps:
                cm_list = configmaps.items  
                if (len(cm_list) > self.scaling_histsize): 
                    #cm_list.sort(key=lambda x: x.metadata.creation_timestamp, reverse=True)
                    cm_list.sort(key=lambda x: x.metadata.resource_version)
                    #logger.debug("sorted list: {}".format(cm_list))
                    cm = cm_list.pop(0)
                    ManageConfig.delete_configmap(self.CM_NAMESPACE, cm.metadata.name)
            return ManageConfig.delete_configmap(self.CM_NAMESPACE, self.CM_NAME)
        except ApiException as ex:
            logger.error("Exception while deleting scaling configmap{}".format(ex))
            raise

if __name__ == "__main__":
    try:
        filepath = "./"
        if not os.path.exists(filepath):
            os.makedirs(filepath)
        logger.setLevel(logging.DEBUG)
        filename = filepath + "psearch_scaling" + datetime.now().strftime("-%Y-%m-%d-%H-%M-%S") + '.log'
        handler = logging.FileHandler(filename)
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        print("Log file is present at {}".format(filename))
        # create console handler and set level to info
        handler = logging.StreamHandler()
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter("%(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        sc = ScalingPolicyConfigmap("test", 10)
        sc.create()
        

    except (KeyboardInterrupt, SystemExit):
        print("Exiting")


