""" Query and patch pravega related k8s resources
"""
import json
import logging
from kubernetes import client, config
from kubernetes.client.rest import ApiException
from scaling.configs.crs import CRs
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

class ManageCustomResource(object):
    """ query and patch k8s custom resources
    """
    NAMESPACE = ''
    
    def __init__(self, cr_name, ns=None, name=None):
        self.NAMESPACE = ns
        cr = CRs.GET(cr_name)
        self.GROUP = cr[CRs.GROUP]
        self.VERSION = cr[CRs.VERSION]
        self.PLURAL = cr[CRs.PLURAL]
        self.NAME = cr[CRs.NAME]
        self.R_NAME = name

    def list(self):
        """ list custom resource for all namespaces
        Args:
        Returns: dict
        Raises: ApiException
        """
        try:
            if self.NAMESPACE == None:
                api_response = api_instance.list_cluster_custom_object(group=self.GROUP,
                                                                       version=self.VERSION,
                                                                       plural=self.PLURAL)
            else:
                api_response = api_instance.list_namespaced_custom_object(group=self.GROUP,
                                                                          version=self.VERSION,
                                                                          plural=self.PLURAL,
                                                                          namespace=self.NAMESPACE)
            return api_response
        except ApiException as ex:
            logger.error("Failed list custom resources, exception {}".format(ex))
            raise

    def get(self):
        """ get custom resource 
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
            # name = 'name_example' # str | the custom object's name.
            api_response = api_instance.get_namespaced_custom_object(group=self.GROUP,
                                                                     version=self.VERSION,
                                                                     namespace=self.NAMESPACE,
                                                                     plural=self.PLURAL,
                                                                     name=self.R_NAME)
            return api_response
        except ApiException as ex:
            logger.error("Failed to get custom resource, exception {}".format(ex))
            raise


    def patch(self, patch):
        """ patch custom resource
        Args: patch (json): patch body in json format
        Returns: object
        Raises: ApiException
        """
        try:
            # https://github.com/kubernetes-client/python/blob/master/kubernetes/docs/CustomObjectsApi.md#patch_namespaced_custom_object
            # group = 'group_example' # str | the custom resource's group
            # version = 'version_example' # str | the custom resource's version
            # namespace = 'namespace_example' # str | The custom resource's namespace
            # plural = 'plural_example' # str | the custom resource's plural name.
            # name = 'name_example' # str | the custom object's name
            # body = kubernetes.client.UNKNOWN_BASE_TYPE() # UNKNOWN_BASE_TYPE | The JSON schema of the Resource to patch.

            logger.info("patching custom with {}".format(patch))

            api_response = api_instance.patch_namespaced_custom_object(group=self.GROUP,
                                                                       version=self.VERSION,
                                                                       namespace=self.NAMESPACE,
                                                                       plural=self.PLURAL,
                                                                       name=self.R_NAME,
                                                                       body=patch)
            logger.debug(json.dumps(api_response, indent=2, sort_keys=True))
            return api_response
        except ApiException as ex:
            logger.error("Failed to patch custom resource with patch {}, exception {}".format(patch, ex))
            raise


