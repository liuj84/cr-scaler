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

api_instance = client.CustomObjectsApi(client.ApiClient(configuration))
logger = logging.getLogger(Constants.LOGGER)

class ManageMetricsResources(object):
    """ query metrics resources
    """
    GROUP = 'metrics.k8s.io'
    VERSION = 'v1beta1'

    def __init__(self, ns):
        self.NAMESPACE = ns

    # apis/metrics.k8s.io/v1beta1/nodes
    def listNodes(self):

        """ get node metrics
        Args:
        Returns: dict
        Raises: ApiException
        """
        PLURAL = 'nodes'
        try:
            # https://github.com/kubernetes-client/python/blob/master/kubernetes/docs/CustomObjectsApi.md#get_namespaced_custom_object
            # group = 'group_example' # str | the custom resource's group
            # version = 'version_example' # str | the custom resource's version
            # namespace = 'namespace_example' # str | The custom resource's namespace
            # plural = 'plural_example' # str | the custom resource's plural name.
            # name = 'name_example' # str | the custom object's name
            api_response = api_instance.list_cluster_custom_object(group=self.GROUP,
                                                                     version=self.VERSION,
                                                                     plural=PLURAL)
            return api_response
        except ApiException as ex:
            logger.error("Failed to list resource, exception {}".format(ex))
            raise

    # apis/metrics.k8s.io/v1beta1/namespaces/test/pods/
    def listPods(self, label_selector = None):
        """ get PravegaSearch resource from project namespace
        Args:
        Returns: dict
        Raises: ApiException
        """
        PLURAL = 'pods'
        try:
            # https://github.com/kubernetes-client/python/blob/master/kubernetes/docs/CustomObjectsApi.md#get_namespaced_custom_object
            # group = 'group_example' # str | the custom resource's group
            # version = 'version_example' # str | the custom resource's version
            # namespace = 'namespace_example' # str | The custom resource's namespace
            # plural = 'plural_example' # str | the custom resource's plural name.
            # name = 'name_example' # str | the custom object's name
            api_response = api_instance.list_namespaced_custom_object(group=self.GROUP,
                                                                     version=self.VERSION,
                                                                     namespace=self.NAMESPACE,
                                                                     label_selector=label_selector,
                                                                     plural=PLURAL)
            return api_response
        except ApiException as ex:
            logger.error("Failed to list resource, exception {}".format(ex))
            raise


    

