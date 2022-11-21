""" kahm event helper
"""
import base64
import logging

import requests
from requests.auth import HTTPBasicAuth
from requests.exceptions import HTTPError
from scaling.resources.manage_config import ManageConfig
from scaling.utils.constants import Constants
logger = logging.getLogger(Constants.LOGGER)

class KahmEvent(object):
    """
    methods to extract kahm secret, send kahm event
    """
    kahm_secret_values = None
    NS = ""

    def __init__(self, ns):
        self.NS = ns

    def get_kahm_secret(self):
        """
        get KAHM secret
        caches secret for next use
        """
        # print("- Getting KAHM secret")
        kahm_secret_values = dict()
        kahm_secret = ManageConfig.get_secret('nautilus-system', 'kahm-restapi-secrets')
        if kahm_secret != None:
            kahm_secret_data = kahm_secret.data
            kahm_cred = kahm_secret_data['credentials.conf']
            if kahm_cred != None:
                kahm_cred_str = base64.b64decode(kahm_cred)
                cred_lines = kahm_cred_str.decode('utf-8').split('\n')
                for line in cred_lines:
                    value = line.split(':')
                    kahm_value = value[1].strip()
                    kahm_secret_values[value[0]] = kahm_value
        self.kahm_secret_values = kahm_secret_values
        return kahm_secret_values
            

    def send_event(self, payload):
        """
        send KAHM event
        Args: 
            payload (json): body of event json format
        """
        if self.kahm_secret_values is None:
            self.kahm_secret_values = self.get_kahm_secret()
        if self.kahm_secret_values is None:
            logging.error("Failed to get kahm-restapi-secrets")
            return
        
        kahm_username = self.kahm_secret_values['username']
        kahm_password = self.kahm_secret_values['password']
        # https://confluence.cec.lab.emc.com:8443/display/ATLANTIC/kahm-restapi
        try:
            resp = requests.post('http://kahm-restapi.nautilus-system.svc.cluster.local:17999/v1/api/events',
                                  headers={'Content-Type':'application/json'},
                                  auth=HTTPBasicAuth(kahm_username, kahm_password),
                                  json=payload)
            logging.debug(resp)
            if resp.status_code != 201:
                logger.error("Failed to send KAHM event {}".format(resp.status_code))
        except HTTPError as e:
            logging.error(e.response.text)



    def send_scaling_started_event(self, message):
        """
        send KAHM event
        Args: 
            payload (json): body of event json format
        """
        # send scaling started event
        event_payload = { "symptomid": "DUMMY-2101",
                          "type": "Info",
                          "component": "obs-scaler",
                          "message": message,
                          "reason": "Scaling Initiated",
                          "appName": "DUMMY-cluster",
                          "namespace": self.NS }
        self.send_event(event_payload)


    def send_scaling_blocked_event(self, elapsed_time, message):
        """
        send KAHM event
        Args: 
            payload (json): body of event json format
        """
        # send scaling started event
        event_payload = { "symptomid": "DUMMY-2103",
                          "type": "Info",
                          "component": "obs-scaler",
                          "elapsedTime": elapsed_time,
                          "message": message,
                          "reason": "Scaling Blocked",
                          "appName": "DUMMY-cluster",
                          "namespace": self.NS}
        self.send_event(event_payload)


    def send_scaling_completed_event(self, message):
        """
        send KAHM event
        Args: 
            payload (json): body of event json format
        """
        event_payload = { "symptomid": "DUMMY-2102",
                          "type": "Info",
                          "component": "obs-scaler",
                          "message": message,
                          "reason": "Scaling Completed",
                          "appName": "DUMMY-cluster",
                          "namespace": self.NS}
        self.send_event(event_payload)

    def send_scaling_failed_event(self, message):
        """
        send KAHM event
        Args:
            payload (json): body of event json format
        """
        event_payload = { "symptomid": "DUMMY-1101",
                          "type": "Warning",
                          "component": "obs-scaler",
                          "message": message,
                          "reason": "Scaling Failed",
                          "appName": "DUMMY-cluster",
                          "namespace": self.NS}
        self.send_event(event_payload)
