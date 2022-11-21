""" query k8s configmap and secret
"""
import json
import logging
import os
import sys

from scaling.configs.workloads import Workloads
from kubernetes.utils.quantity import parse_quantity
from pint import UnitRegistry
from scaling.resources.manage_config import ManageConfig
from scaling.resources.manage_node import ManageNode
from scaling.resources.manage_metrics_resources import ManageMetricsResources
from scaling.utils.yaml_file_helper import YamlFileHelper
from scaling.client.influxdb_client import InfluxClient
from scaling.client.rest_client import RestClient
from scaling.configmaps.scaling_configmap import ScalingConfigmap
from scaling.status import Status
from scaling.utils.constants import Constants
from scaling.configs.config import Config

logger = logging.getLogger(Constants.LOGGER)

class ScalingMetricsConfigmap(ScalingConfigmap):
    scaling_histsize = 10
    YAML_FILE_NAME = "config/scaling_metrics.yaml"
    ureg = UnitRegistry()
    ureg.load_definitions('scaling/utils/kubernetes_units.txt')

    def __init__(self, ns, name, scaling_histsize):    
        self.CM_NAMESPACE = os.environ.get('POD_NAMESPACE')   
        name = os.environ.get('RELEASE')
        self.CM_NAME = "scaling-metrics"
        if name is not None:
            self.CM_NAME = name +"-scaling-metrics"
            label = 'release'
            label_value = name
            self.LABELS = {label: label_value, "component": "cr-scaler"}
        else:
            self.LABELS = {"component": "cr-scaler"}
        self.label_selector = "{}={}".format("component", "cr-scaler")
        self.scaling_histsize = scaling_histsize
        self.rest_client = RestClient(ns)
        self.influxdb_client = InfluxClient(ns)
        self.create()

        
    def create(self):
        if ManageConfig.exist_configmap(self.CM_NAMESPACE, self.CM_NAME):
            return
        print("create config map " + self.CM_NAME)
        values = YamlFileHelper.load_values(self.YAML_FILE_NAME)
        cm_data_from_yaml = values['data']
        return ManageConfig.create_configmap(self.CM_NAMESPACE, self.CM_NAME, cm_data_from_yaml, self.LABELS, generate=False)


    def update_values(self, policy_data, current_status: Status):
        # http://localhost:8001/apis/metrics.k8s.io/v1beta1/namespaces/test/pods/psearch-shardworker-0
        cm_data = dict()
        patch = dict()
        patch["data"] = dict()
        resource_usage = dict()
        self.update_pods_resource_usage(resource_usage)
        self.update_nodes_resource_usage(resource_usage)
        
        for item in policy_data:
            cm_data[item] = dict()
            if item != "node" and len(resource_usage["cpu_usage"][item])>0:
                policy_json = json.loads(policy_data[item])
                metrics_all = {item['name'] for item in policy_json["metrics"]}
                if "retrict" in policy_json:
                    metrics_all = metrics_all | {item['name'] for item in policy_json["retrict"]}
                for policy in metrics_all:
                    p = policy.split("##")
                    if len(p) == 4:
                        if p[1] == Config.METRICS_TYPE_INFLUX:
                            cm_data[item][policy] = dict()
                            # average / total
                            cm_data[item][policy]["totalValue"] = self.influxdb_client.get_value(p[2], p[3])
                        elif p[1] == Config.METRICS_TYPE_REST:
                            cm_data[item][policy] = dict()
                            cm_data[item][policy]["totalValue"] = self.rest_client.get_value(p[2], p[3])
                cm_data[item]["cpu"] = dict()
                cm_data[item]["cpu_m"] = dict()
                request_cpu = current_status.get_requests_cpu()[item]
                current_cpu = resource_usage["cpu_usage"][item]
                cm_data[item]["cpu"]["averageValue"] = self.calculate_percentage(current_cpu, request_cpu)
                cm_data[item]["cpu_m"]["averageValue"] = str(sum(parse_quantity(v) for v in current_cpu) / len(current_cpu) * 1000)

                cm_data[item]["memory"] = dict()
                cm_data[item]["memory_M"] = dict()
                request_memory = current_status.get_requests_memory()[item]
                current_memory = resource_usage["memory_usage"][item]
                cm_data[item]["memory"]["averageValue"] = self.calculate_percentage(current_memory, request_memory)
                cm_data[item]["memory_M"]["averageValue"] = str(sum(parse_quantity(v) for v in current_memory) / len(current_memory) / 1000000)
                
                patch["data"][item] = json.dumps(cm_data[item], indent=2)  

        cm_data["node"]["cpu"] = dict()
        cm_data["node"]["memory"] = dict()
        cm_data["node"]["cpu_m"] = dict()
        cm_data["node"]["memory_M"] = dict()
        total_cpu_capacity = sum(parse_quantity(v) for v in resource_usage["node_cpu_capacity"])
        total_memory_capacity = sum(parse_quantity(v) for v in resource_usage["node_memory_capacity"])
        average_cpu_capacity = total_cpu_capacity / len(resource_usage["node_cpu_capacity"])
        average_memory_capacity = total_memory_capacity / len(resource_usage["node_memory_capacity"])
        cm_data["node"]["cpu"]["averageValue"] = self.calculate_percentage(resource_usage["node_cpu_usage"],average_cpu_capacity)
        cm_data["node"]["memory"]["averageValue"] = self.calculate_percentage(resource_usage["node_memory_usage"], average_memory_capacity)
        cm_data["node"]["cpu_m"]["totalValue"] = str(sum(parse_quantity(v) for v in resource_usage["node_cpu_usage"]) * 1000)
        cm_data["node"]["memory_M"]["totalValue"] = str(sum(parse_quantity(v) for v in resource_usage["node_memory_usage"]) / 1000000)
        cm_data["node"]["cpu_m"]["totalCapacity"] = str(total_cpu_capacity * 1000)
        cm_data["node"]["memory_M"]["totalCapacity"] = str(total_memory_capacity / 1000000)
        
        patch["data"]["node"] = json.dumps(cm_data["node"], indent=2)  
        # self.update_index_shard_metrics(cm_data, current_status)
        self.patch(patch)
        logger.info("New scaling_metrics values: {}".format(cm_data))
        return

    # def update_nodes_resource_usage(self, current_status):
    def update_pods_resource_usage(self, resource_usage):
        cpu_usage = dict()
        memory_usage = dict()
        for workload in Workloads.LIST_WORKLOAD_NAMES():
            label_selector = Workloads.GET_WORKLOAD_SELECTOR(workload)
            metrics = ManageMetricsResources(self.CM_NAMESPACE).listPods(label_selector)
            cpu_usage[workload] = []
            memory_usage[workload] = []
            container_name = Workloads.GET_WORKLOAD_CONTAINER_NAME(workload)
            if "items" in metrics:
                for item in metrics["items"]:
                    for container in item["containers"]:
                        if container["name"] == container_name:
                            cpu_usage[workload].append(container["usage"]["cpu"])
                            memory_usage[workload].append(container["usage"]["memory"])
                    
        resource_usage["cpu_usage"] = cpu_usage
        resource_usage["memory_usage"] = memory_usage

    def update_nodes_resource_usage(self, resource_usage):
        node_metrics = ManageMetricsResources(self.CM_NAMESPACE).listNodes()
        node_info = ManageNode().list()
        cpu_usage = []
        memory_usage = []
        if "items" in node_metrics:
            for item in node_metrics["items"]:
                cpu_usage.append(item["usage"]["cpu"])
                memory_usage.append(item["usage"]["memory"])
        resource_usage["node_cpu_usage"] = cpu_usage
        resource_usage["node_memory_usage"] = memory_usage

        cpu_capacity = []
        memory_capacity = []
        for item in node_info.items:
            cpu_capacity.append(item.status.capacity['cpu'])
            memory_capacity.append(item.status.capacity['memory'])
        resource_usage["node_cpu_capacity"] = cpu_capacity
        resource_usage["node_memory_capacity"] = memory_capacity

    def calculate_percentage(self, current_value, request_value):
        value = sum(parse_quantity(v) for v in current_value) / len(current_value) / parse_quantity(request_value) * 100
        logger.debug("current {}, request {}, val {} ".format(current_value, request_value, value))
        return str(value)



