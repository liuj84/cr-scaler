import imp
import json
import logging
import os
import sys
import time
from datetime import datetime
from xml.dom.minidom import Element


sys.path.append(os.getcwd())
from scaling.kahm_event import KahmEvent
from scaling.utils.constants import Constants
from scaling.configs.workloads import Workloads
from scaling.provisioner import Provisioner
from scaling.client.rest_client import RestClient
from scaling.configmaps.scaling_metrics import ScalingMetricsConfigmap
from scaling.configmaps.scaling_policy import ScalingPolicyConfigmap
from scaling.configs.config import Config
from scaling.status import Status
from scaling.resources.manage_custom_object import ManageCustomResource

logger = logging.getLogger(Constants.LOGGER)

class ScalingJob(object):
    SLEEP_INTERVAL_SEC = 10
    KAHM_ALERT_INTERVAL = 900    # seconds
    SCALING_START_TIME = SCALING_ALERT_TIME = time.time()

    def __init__(self, ns, name, manage_cluster_cr: ManageCustomResource):
        self.NS = ns
        self.NAME = name
        self.manage_cluster_cr = manage_cluster_cr
        self.metrics_configmap = ScalingMetricsConfigmap(ns, name, Constants.SCALING_HISTSIZE)
        self.policy_configmap = ScalingPolicyConfigmap(ns, name, Constants.SCALING_HISTSIZE)
        self.cr_status = Status(ns, name, self.manage_cluster_cr)
        self.rest_client = RestClient(ns)
        self.kahm_event = KahmEvent(ns)


    def main(self):
        if not self.check_scaling_status():
            return
        self.policy_configmap.update_replicas(self.cr_status.get_defined_replicas())
        policy_data = self.policy_configmap.get().data

        self.metrics_configmap.update_values(policy_data, self.cr_status)
        metrics_data = self.metrics_configmap.get().data

        provisioner = Provisioner(metrics_data, policy_data, self.cr_status.get_replicas(), self.NS)
        newValues = provisioner.provision()
        if newValues is None:
            return
        logger.info("scaling policy: {}".format(policy_data))
        logger.info("current status: {}".format(self.cr_status.get_status()))
        logger.info("new values: {}".format(newValues))
        scaled = False
        for workload in newValues:
            scaled = self.scale_workload(self.cr_status.get_defined_replicas(workload), newValues[workload], workload) or scaled
        if scaled:
            self.handle_scaling_completed()

    def getCurrentReplica(self, current_status, type):
        return int(current_status["replicas"][type])

    def check_scaling_status(self):
        return self.cr_status.is_ready()

    def is_scale_needed(self, current_replcia, newValue):
        return int(current_replcia) != int(newValue)

    def scale_workload(self, current_replica, newValue, workload):
        if not self.is_scale_needed(current_replica, newValue):
            logger.info("No need to scale {}".format(workload))
            return False
        if not self.check_scaling_status():
            logger.info("scaling {} skipped since cluster status is not ready".format(workload))
            return False
        data = dict()
        # pravega/controllerReplicas
        path_element = Workloads.GET_WORKLOAD_REPLICAS_PATH(workload).strip("/").split("/")
        path_element.reverse()
        element = dict()
        val = newValue
        for x in path_element:
            element[x] = val
            val = element
            element = dict()
        patch = val
        msg = "Scale workload {} with {}".format(workload, patch)
        logger.info(msg)
        # self.kahm_event.send_scaling_started_event(msg)
        self.manage_cluster_cr.patch(patch)
        self.monitor_scale_status(workload, workload, newValue)
        return True

    def monitor_scale_status(self, type, name, desired_replica_count):
        """
        monitor scale status
        """
        self.SCALING_START_TIME = self.SCALING_ALERT_TIME = time.time()
        while True:
            status = self.cr_status.get_current_status()
            logger.info(status)

            if status['replicas'][type] != desired_replica_count:
                logger.info("{} scaling values are not applied yet or operator has not reconciled, waiting".format(name))
                self.send_scaling_blocked_event(type, name, desired_replica_count, status)
                time.sleep(self.SLEEP_INTERVAL_SEC)
                self.SCALING_START_TIME = self.SCALING_ALERT_TIME = time.time()
                continue
            if int(status['replicas'][type]) != int(status['ready_replicas'][type]):
                logger.info("waiting for replicas to be ready")
                self.send_scaling_blocked_event(type, name, desired_replica_count, status)
                time.sleep(self.SLEEP_INTERVAL_SEC)
                continue
            else:
                logger.info("{} scaling finished".format(name))
                break

    def send_scaling_blocked_event(self, type, name, desired_replica_count, status):
        """
        send scaling blocked event if scaling has not completed in KAHM_ALERT_INTERVAL
        """
        current_time = time.time()
        elapsed_time = current_time - self.SCALING_ALERT_TIME
        if elapsed_time > self.KAHM_ALERT_INTERVAL:
            msg_object = dict()
            msg_object['name'] = name
            msg_object['type'] = type
            msg_object['status'] = status
            msg_object['desired_replicas'] = desired_replica_count
            message = json.dumps(msg_object)
            logger.warning(message)
            # self.kahm_event.send_scaling_blocked_event(
            #     time.strftime("%H:%M:%S", time.gmtime(current_time - self.SCALING_START_TIME)),
            #     message)
            self.SCALING_ALERT_TIME = current_time

    def handle_scaling_completed(self):
        """
        send scaling completed event
        """
        msg_object = dict()
        msg_object['current_status'] = self.cr_status.get_current_status()
        msg_object['metrics'] = self.metrics_configmap.get().data
        # self.kahm_event.send_scaling_completed_event(json.dumps(msg_object))

if __name__ == "__main__":
    try:
        filepath = "./"
        if not os.path.exists(filepath):
            os.makedirs(filepath)
        logger.setLevel(logging.DEBUG)
        filename = filepath + "scaling" + datetime.now().strftime("-%Y-%m-%d-%H-%M-%S") + '.log'
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

        sc = ScalingJob("test")
        sc.main()
    except (KeyboardInterrupt, SystemExit):
        print("Exiting")
