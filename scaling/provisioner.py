import json
import logging
import math
import os
import sys
from scaling.configs.workloads import Workloads
from scaling.utils.constants import Constants
from scaling.kahm_event import KahmEvent

sys.path.append(os.getcwd())

logger = logging.getLogger(Constants.LOGGER)

class Provisioner(object):
    def __init__(self, metrics, policy, current_replicas, ns):
        self.metrics = metrics
        self.policy = policy
        self.current_replicas = current_replicas
        self.cpu_delta = 0.0
        self.memory_delta = 0.0
        self.kahm_event = KahmEvent(ns)
 
    def provision(self):
        newValues = dict()
        self.cpu_delta = 0
        self.memory_delta = 0
        for workload in Workloads.LIST_WORKLOAD_NAMES():
            newValues[workload] = self.calculate_value(workload)

        node_resource_sufficient = self.node_resource_sufficient()
        if not node_resource_sufficient:
            msg = "Scaling skipped due to insufficient system resource"
            logger.warning(msg)
            # self.kahm_event.send_scaling_failed_event(msg)
            return None
        return newValues

    def calculate_value(self, type):
        logger.info("calculate {} replicas, metrics {}, policy {}, current replicas {}".format(type, self.metrics[type], self.policy[type], self.current_replicas[type]))
        return self.calculate_replicas(self.metrics[type], self.policy[type], self.current_replicas[type])

    def node_resource_sufficient(self):
        policy = json.loads(self.policy['node'])
        metrics = json.loads(self.metrics['node'])
        for p in policy["metrics"]:
            name = p["name"]
            target_total_value = p["targetTotalValue"]
            if name == "cpu":
                metrics_name = "cpu_m"
                delta = self.cpu_delta
            elif name == "memory":
                metrics_name = "memory_M"
                delta = self.memory_delta
            logger.debug("policy: {}, targetTotalValue: {}".format(name, target_total_value))
            if "totalValue" in metrics[metrics_name] and "totalCapacity" in metrics[metrics_name]:
                ratio = float((float(metrics[metrics_name]["totalValue"]) + delta) / float(metrics[metrics_name]["totalCapacity"]))  * 100
                if ratio > float(target_total_value):
                    return False
        return True

    def calculate_replicas(self, workload_metrics, workload_policy, workload_replica):
        metrics = json.loads(workload_metrics)
        policy = json.loads(workload_policy)
        min_replicas = policy["minReplicas"]
        max_replicas = policy["maxReplicas"]
        desiredReplicas = min_replicas
        for p in policy["metrics"]:
            name = p["name"]
            target_average_value = p["targetAverageValue"]
            if name in metrics:
                logger.debug("metrics: {}, targetAverageValue: {}".format(name, target_average_value))
                if "averageValue" in metrics[name]:
                    calcReplicas = math.ceil(int(workload_replica) * (float(metrics[name]["averageValue"]) / float(target_average_value)))
                    logger.info("metrics: {}, targetAverageValue: {}, metricsAverageValue {}, calcReplicas: {}, min: {}, max: {}"
                                 .format(name, target_average_value, metrics[name]["averageValue"], calcReplicas, min_replicas, max_replicas))
                    calcReplicas = min(max(calcReplicas, min_replicas), max_replicas)
                    desiredReplicas = max(calcReplicas, desiredReplicas)
                elif "totalValue" in metrics[name]:
                    calcReplicas = math.ceil(float(metrics[name]["totalValue"]) / float(target_average_value))
                    logger.info("metrics: {}, targetAverageValue: {}, metricsTotalValue {}, calcReplicas: {}, min: {}, max: {}"
                                 .format(name, target_average_value, metrics[name]["totalValue"], calcReplicas, min_replicas, max_replicas))

                    calcReplicas = min(max(calcReplicas, min_replicas), max_replicas)
                    desiredReplicas = max(calcReplicas, desiredReplicas)
        if "restrict" in policy:
            for p in policy["restrict"]:
                name = p["name"]
                target_average_value = p["targetAverageValue"]
                if name in metrics:
                    logger.debug("restrict: {}, targetAverageValue: {}".format(name, target_average_value))
                    if "averageValue" in metrics[name]:
                        calcReplicas = math.floor(int(workload_replica) * (float(metrics[name]["averageValue"]) / float(target_average_value)))
                        logger.info("restrict: {}, targetAverageValue: {}, metricsAverageValue {}, calcReplicas: {}, min: {}, max: {}"
                                     .format(name, target_average_value, metrics[name]["averageValue"], calcReplicas, min_replicas, max_replicas))
                        calcReplicas = min(max(calcReplicas, min_replicas), max_replicas)
                        desiredReplicas = min(calcReplicas, desiredReplicas)
                    elif "totalValue" in metrics[name]:
                        calcReplicas = math.floor(float(metrics[name]["totalValue"]) / float(target_average_value))
                        logger.info("restrict: {}, targetAverageValue: {}, metricsTotalValue {}, calcReplicas: {}, min: {}, max: {}"
                                     .format(name, target_average_value, metrics[name]["totalValue"], calcReplicas, min_replicas, max_replicas))

                        calcReplicas = min(max(calcReplicas, min_replicas), max_replicas)
                        desiredReplicas = min(calcReplicas, desiredReplicas)
        if "scaleUpEnabled" in policy and policy["scaleUpEnabled"].lower() == "false":
            # scale up is not allowed
            desiredReplicas = min(workload_replica, desiredReplicas)
        if "scaleDownEnabled" in policy and policy["scaleDownEnabled"].lower() == "false":
            # scale down is not allowed
            desiredReplicas = max(workload_replica, desiredReplicas)

        delta = desiredReplicas - workload_replica
        if "cpu_m" in metrics:
            cpu_delta = delta * float(metrics["cpu_m"]["averageValue"])
            self.cpu_delta += cpu_delta
        if "memory_M" in metrics:
            memory_delta = delta * float(metrics["memory_M"]["averageValue"])
            self.memory_delta += memory_delta
        logger.info("Desired replicas: {}".format(desiredReplicas))
        return desiredReplicas

    