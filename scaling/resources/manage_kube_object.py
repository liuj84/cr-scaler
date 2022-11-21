""" Query and patch pravega related k8s resources
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

configuration.debug = False
configuration.logger["package_logger"] = logging.getLogger("client")
configuration.logger["urllib3_logger"] = logging.getLogger("urllib3")

api_instance = client.AppsV1Api(client.ApiClient(configuration))
logger = logging.getLogger(Constants.LOGGER)

class ManageKubeResource(object):
    """ query and patch k8s resources
    """
    NAMESPACE = ''
    GROUP = 'apps'
    VERSION = 'v1'
    
    def __init__(self, ns=None, name=None):
        self.NAMESPACE = ns
        self.NAME = name

    def list_sts(self, label_selector=None):
        """ list sts resource
        Args:
        Returns: dict
        Raises: ApiException
        """
        try:
            if self.NAMESPACE == None:
                api_response = api_instance.list_stateful_set_for_all_namespaces(label_selector = label_selector)
            else:
                api_response = api_instance.list_namespaced_stateful_set(self.NAMESPACE, label_selector = label_selector)
            return api_response
        except ApiException as ex:
            logger.error("Failed list sts, exception {}".format(ex))
            raise

    def list_deploy(self, label_selector=None):
        """ list deploy resource
        Args:
        Returns: dict
        Raises: ApiException
        """
        try:
            if self.NAMESPACE == None:
                api_response = api_instance.list_deployment_for_all_namespaces(label_selector = label_selector)
            else:
                api_response = api_instance.list_namespaced_deployment(self.NAMESPACE, label_selector = label_selector)
            return api_response
        except ApiException as ex:
            logger.error("Failed list deploy, exception {}".format(ex))
            raise




