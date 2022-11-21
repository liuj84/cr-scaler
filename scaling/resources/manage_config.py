""" query k8s configmap and secret
"""

import logging
from kubernetes import client, config
from kubernetes.client.rest import ApiException
from scaling.utils.constants import Constants
configuration = client.Configuration()
try:
    config.load_incluster_config(configuration)
except config.config_exception.ConfigException as ex:
    config.load_kube_config(client_configuration=configuration)

api_instance = client.CoreV1Api(client.ApiClient(configuration))
logger = logging.getLogger(Constants.LOGGER)

class ManageConfig(object):
    """ methods to query k8s configmap and secret
    uses the following kubernetes-client API
    https://github.com/kubernetes-client/python/blob/master/kubernetes/docs/CoreV1Api.md
    https://github.com/kubernetes-client/python/blob/master/kubernetes/docs/V1ConfigMap.md
    """

    @staticmethod
    def get_configmap(namespace, name):
        """ get k8s configmap
        Args:
            namespace (str): namespace
            name (str): name of configmap
        Returns: V1ConfigMap
        Raises: ApiException
        """
        try:
            api_response = api_instance.read_namespaced_config_map(name, namespace)
            return api_response
        except ApiException as ex:
            if ex.status == 404:
                logger.debug("configmap is not found {}".format(name))
            else:
                logger.error("Failed to get configmap {}, exception {}".format(name, ex))
            raise

    @staticmethod
    def exist_configmap(namespace, name):
        """ check if k8s configmap exist
        Args:
            namespace (str): namespace
            name (str): name of configmap
        Returns: bool
        Raises: ApiException
        """
        try:
            api_response = api_instance.read_namespaced_config_map(name, namespace)
            return True
        except ApiException as ex:
            if ex.status == 404:
                return False
            else:
                logger.error("Failed to get configmap {}, exception {}".format(name, ex))
            raise

    @staticmethod
    def list_configmap(namespace, label_selector):
        """ list namespaced configmaps
        Args:
            namespace (str): namespace
            label_selector (str=str): label=value
        Returns: V1ConfigMapList
        Raises: ApiException
        """
        try:
            api_response = api_instance.list_namespaced_config_map(namespace, label_selector=label_selector)
            return api_response
        except ApiException as ex:
            logger.error("Failed to list configmaps, exception {}".format(ex))
            raise


    @staticmethod
    def create_configmap(namespace, name, data, labels, generate=False):
        """ create k8s configmap
        Args:
            namespace (str): namespace
            name (str): name of configmap
            data (str): data in json format
            generate (bool): True to use name argument as prefix
        Returns: V1ConfigMap
        Raises: ApiException
        """
        try:
            body = client.V1ConfigMap()
            if generate:
                body.metadata = client.V1ObjectMeta(generate_name=name,labels=labels)
            else:
                body.metadata = client.V1ObjectMeta(name=name,labels=labels)
            body.data = data
            api_response = api_instance.create_namespaced_config_map(namespace, body)
            return api_response
        except ApiException as ex:
            if ex.status == 409:
                logger.debug("configmap already exists: {}".format(name))
            else:
                logger.error("Failed to create configmap, exception {}".format(ex))
            raise


    @staticmethod
    def copy_configmap(namespace, name, new_name, new_labels, generate=True):
        """ 
        Args:
            namespace (str): namespace
            name (str): name of configmap
            new_name (str): new name of configmap
            generate (bool): if True new_name will be used as prefix and k8s will generate suffix
        Returns: V1ConfigMap
        Raises: ApiException
        """
        try:
            configmap = ManageConfig.get_configmap(namespace, name)
            api_response = ManageConfig.create_configmap(namespace, new_name, \
                configmap.data, new_labels, generate=generate)
            return api_response
        except ApiException as ex:
            if ex.status == 404:
                logger.debug("configmap is not found: {}".format(name))
            else:
                logger.error("Failed to copy configmap from {} to {}, exception {}".format(name, new_name, ex))
            raise


    @staticmethod
    def patch_configmap(namespace, name, data):
        """ create k8s configmap
        Args:
            namespace (str): namespace
            name (str): name of configmap
            data (str): data in json format
        Returns: V1ConfigMap
        Raises: ApiException
        """
        try:
            api_response = api_instance.patch_namespaced_config_map(name, namespace, body=data)
            return api_response
        except ApiException as ex:
            logger.error("Failed to patch configmap {} in {}, exception {}".format(name, namespace, ex))
            raise


    @staticmethod
    def delete_configmap(namespace, name):
        """ delete k8s configmap
        Args:
            namespace (str): namespace
            name (str): name of configmap
        Returns: V1ConfigMap
        Raises: ApiException
        """
        try:
            api_response = api_instance.delete_namespaced_config_map(name, namespace)
            logger.debug("{}".format(api_response))
            return api_response
        except ApiException as ex:
            logger.error("Failed to delete configmap, exception {}".format(ex))
            raise

    @staticmethod
    def get_secret(namespace, name):
        """ get k8s secret
        Args:
            namespace (str): namespace
            name (str): name of secret
        Returns: V1Secret
        Raises: ApiException
        """
        try:
            api_response = api_instance.read_namespaced_secret(name, namespace)
            return api_response
        except ApiException as ex:
            logger.error("Failed to get secret, exception {}".format(ex))
            raise

