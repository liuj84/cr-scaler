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

api_instance = client.CoreV1Api(client.ApiClient(configuration))
logger = logging.getLogger(Constants.LOGGER)


class ManageNode(object):
    """ query and patch k8s resources related to pravega
    """
    GROUP = 'api'
    VERSION = 'v1'
    PLURAL = 'nodes'


    # api/v1/nodes
    def list(self):

        """ get nodes
        Args:
        Returns: dict
        Raises: ApiException
        """
        try:
            # https://github.com/kubernetes-client/python/blob/master/kubernetes/docs/CustomObjectsApi.md#get_namespaced_custom_object
            # group = 'group_example' # str | the custom resource's group
            # version = 'version_example' # str | the custom resource's version
            # namespace = 'namespace_example' # str | The custom resource's namespace
            # plural = 'plural_example' # str | the custom resource's plural name.
            # name = 'name_example' # str | the custom object's name
            api_response = api_instance.list_node()
            return api_response
        except ApiException as ex:
            logger.error("Failed to list resource, exception {}".format(ex))
            raise



