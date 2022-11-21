""" query k8s configmap and secret
"""
import json
import logging
from scaling.resources.manage_config import ManageConfig
from kubernetes.client.rest import ApiException
from scaling.utils.constants import Constants

logger = logging.getLogger(Constants.LOGGER)

class ScalingConfigmap(object):
    """ CRUD for scaling-configmap
    """

    CURRENT_VALUES_YAML = "current-values.yaml"
    SCALING_VALUES_YAML = "scaling-values.yaml"
    CM_NAME = "scaler-cm"
    CM_NAMESPACE = ""
    CM_NAME_PREFIX = "scale-"
    scaling_histsize = 10

    def __init__(self, scaling_histsize, ns):
        self.scaling_histsize = scaling_histsize
        self.CM_NAMESPACE = ns

    def create(self, current_values, scaling_values):
        """create configmap for scaling job
        TODO: retry if ApiException return status is 201 or 500" (see generate_name)
        https://github.com/kubernetes-client/python/blob/master/kubernetes/docs/V1ObjectMeta.md
        Args: data_dict (dict): dictionary which can be converted into json and
            saved into data of configmap
        Returns: V1ConfigMap
        Raises: ApiException
        """
        cm_data = dict()
        cm_data[self.CURRENT_VALUES_YAML] = json.dumps(current_values, indent=2)
        cm_data[self.NEW_VALUES_YAML] = json.dumps(scaling_values, indent=2)
        for key in self.status_keys:
            cm_data[key] = self.STATUS_NONE
        try:
            api_response = ManageConfig.create_configmap(self.CM_NAMESPACE, self.CM_NAME, cm_data, self.LABELS,
                                                         generate=False)
        except ApiException as ex:
            if ex.status == 409:
                current_cm = ManageConfig.get_configmap(self.CM_NAMESPACE, self.CM_NAME)
                current_cm_data = current_cm.data
                # check if existing configmap is same
                if current_cm_data[self.CURRENT_VALUES_YAML] == cm_data[self.CURRENT_VALUES_YAML] and \
                        current_cm_data[self.NEW_VALUES_YAML] == cm_data[self.NEW_VALUES_YAML]:
                    return current_cm
                else:
                    scaling_status = self.get_scaling_status(current_cm)
                    if self.is_scaling_completed(scaling_status):
                        logger.info("This cluster has been scaled previously, scaling configuration already exists")
                    else:
                        logger.info(
                            "Scaling of this cluster was initiated, but it is not complete, did you run decks-installer apply the values?")

            raise

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
        configmaps = ManageConfig.list_configmap(self.CM_NAMESPACE, self.LABEL_SELECTOR)
        return configmaps


    def sorted_list(self, reverse=True):
        """get scaling configmap
        Args:
        Returns: list[V1ConfigMap]
        Raises: ApiException
        """
        configmaps = ManageConfig.list_configmap(self.CM_NAMESPACE, self.LABEL_SELECTOR)
        if configmaps:
            cm_list = configmaps.items  
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
            configmaps = ManageConfig.list_configmap(self.CM_NAMESPACE, self.LABEL_SELECTOR)
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
        


    def get_manifest(self, configmap=None):
        """get manifest in the form of psearch_manifest used to install psearch
        Args:
        Returns: dict
        Raises: ApiException
        """
        manifest = None
        if not configmap:
            configmap = ManageConfig.get_configmap(self.CM_NAMESPACE, self.CM_NAME)
        if configmap:
            configmap_dict = configmap.data
            if configmap_dict is not None:
                manifest = json.loads(configmap_dict[self.SCALING_VALUES_YAML])
        return manifest


