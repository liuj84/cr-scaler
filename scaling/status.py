""" Query status of all pravega members status blocks of related k8s resources
"""
import logging
from operator import truediv
import os
import sys
from kubernetes.client.rest import ApiException
sys.path.append(os.getcwd())
from scaling.resources.manage_custom_object import ManageCustomResource
from scaling.resources.manage_kube_object import ManageKubeResource
from scaling.utils.constants import Constants
from scaling.configs.workloads import Workloads

logger = logging.getLogger(Constants.LOGGER)

class Status(object):
    """ query custom objects
    """
    def __init__(self, ns, name, manage_cluster_cr: ManageCustomResource):

        self.manage_cluster_cr = manage_cluster_cr
        self.manage_kube = ManageKubeResource(ns, name)
        self.status = dict()


    def get_current_status(self):
        """ get current status of all pravega members: zk, bk, ss, controller
        Args:
        Returns: dictionary
        Raises: ApiException
        """
        self.status = dict()
        generation = 0
        resource_version = ""
        self.status["component_ready"] = dict() 
        self.status["defined_replicas"] = dict()  
        self.status["replicas"] = dict()  
        self.status["ready_replicas"] = dict()  # replicas defined in spec
        self.status["requests_cpu"] = dict()   
        self.status["requests_memory"] = dict()

        workloads = Workloads.LIST_WORKLOAD_NAMES()

        cluster = self.manage_cluster_cr.get()        
        if cluster and "status" in cluster:
            for workload in workloads:
                self.fill_workload_status(workload, cluster, self.status)

            if 'metadata' in cluster:
                generation = cluster['metadata']['generation']
                resource_version = cluster['metadata']['resourceVersion']

        logger.debug("Current status")
        logger.debug("Custom object generation: {}, resource version: {}" \
            .format(generation, resource_version))
        logger.debug("Status: {}".format(self.status))
        return self.status

    def fill_workload_status(self, workload, cluster, current_status):
        self.fill_defined_replicas(workload, cluster, current_status)
        self.fill_ready_status(workload, cluster, current_status)
        self.fill_pod_status(workload, current_status)

    def get_status(self):
        if len(self.status) == 0:
            self.get_current_status()
        return self.status

    def get_replicas(self, type=None):
        if type is None:
            return self.get_status()["replicas"]
        else:
            return self.get_status()["replicas"][type]
    
    def get_defined_replicas(self, type=None):
        if type is None:
            return self.get_status()["defined_replicas"]
        else:
            return self.get_status()["defined_replicas"][type]

    def get_ready_replicas(self):
        return self.get_status()["ready_replicas"]

    def get_requests_cpu(self):
        return self.get_status()["requests_cpu"]

    def get_requests_memory(self):
        return self.get_status()["requests_memory"]

    def is_ready(self):
        ready = True
        for comp in self.get_status()["component_ready"].values():
            ready = ready & comp
        return ready
    
    def fill_ready_status(self, workload, cluster, current_status):
        try:
            items = Workloads.GET_WORKLOAD_STATUS_CHECKER(workload)
            ready = True
            for item in items:
                path = item[Workloads.ATTR_STATUS_CHECKER_PATH]
                value = item[Workloads.ATTR_STATUS_CHECKER_VALUE]
                element = cluster
                for x in path.strip("/").split("/"):
                    element = element[x]
                if str(element).lower() != str(value).lower():
                    ready = False
                    break
            current_status["component_ready"][workload] = ready
        except:
            logger.info("{} fill_ready_status failed".format(workload))

    def fill_defined_replicas(self, workload, cluster, current_status):
        try:
            component = workload.split('.')[0]
            paths = Workloads.GET_WORKLOAD_REPLICAS_PATH()
            element = cluster
            if workload in paths:
                for x in paths[workload].strip("/").split("/"):
                    element = element[x]
            if element <= Workloads.GET_WORKLOAD_MIN_REPLICAS(workload):
                element = Workloads.GET_WORKLOAD_MIN_REPLICAS(workload)
            current_status["defined_replicas"][workload] = element
        except:
            logger.info("{} fill_defined_replicas failed".format(workload))

    def fill_pod_status(self, workload, current_status):
        try:
            label_selector = Workloads.GET_WORKLOAD_SELECTOR(workload)
            resp = None
            type = Workloads.GET_WORKLOAD_TYPE(workload)
            if (type == 'sts'):
                resp = self.manage_kube.list_sts(label_selector)
            elif (type == 'deploy'):
                resp = self.manage_kube.list_deploy(label_selector)
            if resp is not None and len(resp.items) > 0:
                item = resp.items[0]
                current_status["ready_replicas"][workload] = item.status.ready_replicas
                current_status["replicas"][workload] = item.status.replicas
                requests = item.spec.template.spec.containers[0].resources.requests
                current_status["requests_cpu"][workload] = requests['cpu']
                current_status["requests_memory"][workload] = requests['memory']
        except:
            logger.info("{} fill_pod_status failed".format(workload))
