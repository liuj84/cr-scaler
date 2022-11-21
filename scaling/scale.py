"""
script to help in scaling the cluster
"""
#!/usr/bin/env python3
#
# Scale SDP cluster
#
# Prerequisites:
# additional ESXi hosts added to vCenter and exposed to PKS.
# pks resize is run to expand nautilus cluster (increase k8s worker nodes)
#
# Process Description:
# Logs messages to cluster_scaling-<timestamp>.log
# Performs healthchecks prior to starting scaling process.
# Queries worker nodes to get allocated and allocatable resources.
# Uses pravega-prvisioner's recommended values
# Updates install values file with new values
# Creates configmap for scaling batch job
# Monitors scaling
#

from datetime import datetime
import logging
import os
import sys
import traceback

sys.path.append(os.getcwd())
from scaling.resources.manage_custom_object import ManageCustomResource
from scaling.scaling_job import ScalingJob
from scaling.configs.crs import CRs
from scaling.utils.constants import Constants
from scaling.configmaps.scaler_config import ScalerConfigConfigmap

class Scale(object):
    """ helper methods needed to scale the cluster
    """

    def __init__(self):
        self.NS = os.environ.get('POD_NAMESPACE')
        self.CR = CRs.GET_MAIN_CR_NAME()
        self.cluster_cr = ManageCustomResource(self.CR, ns=self.NS)

    def main(self):
        self.scale()

    def scale(self):
        """ do scaling
        """
        listResponse = self.cluster_cr.list()
        if len(listResponse['items']) == 0:
            logger.info("No cluster found")
            return
        for cluster in listResponse['items']:
            try:
                cr = ManageCustomResource(self.CR, cluster["metadata"]["namespace"], cluster["metadata"]["name"])
                logger.info(
                    "=== Scaling {}/{} ===".format(cluster["metadata"]["namespace"], cluster["metadata"]["name"]))
                ScalingJob(cluster["metadata"]["namespace"], cluster["metadata"]["name"], cr).main()
                logger.info(
                    "=== Scaling {}/{} finished ===".format(cluster["metadata"]["namespace"], cluster["metadata"]["name"]))
            except Exception as e:
                logger.error(
                    "{}/{} scaling failed with error {}".format(cluster["metadata"]["namespace"], cluster["metadata"]["name"], e, exc_info=True, stack_info=True))
                traceback.print_exc(file=sys.stdout)

if __name__ == "__main__":
    try:
        filepath = "scaling/logs/"
        if not os.path.exists(filepath):
            os.makedirs(filepath)
        logger = logging.getLogger(Constants.LOGGER)
        logger.setLevel(logging.DEBUG)
        filename = filepath + "scaler" + datetime.now().strftime("-%Y-%m-%d-%H-%M-%S") + '.log'
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

        sc = Scale()
        sc.main()

    except (KeyboardInterrupt, SystemExit):
        print("Exiting")
