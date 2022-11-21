import os,json
from scaling.utils.yaml_file_helper import YamlFileHelper
from scaling.configmaps.scaler_config import ScalerConfigConfigmap


class Config(object):
    """
    methods to extract kahm secret, send kahm event
    """
    kahm_secret_values = None

    CRS = "crs"
    WORKLOADS = "workloads"
    METRICS_PROVIDERS = "metrics-providers"
    METRICS_INFLUXDBS = "influxdbs"
    METRICS_REST = "rests"
    METRICS_TYPE_INFLUX = "influx"
    METRICS_TYPE_REST = "rest"
    config_cm = ScalerConfigConfigmap()
    VALUES = json.loads(config_cm.get().data["data"])

    def SET_VALUES(values):
        Config.VALUES = values

    def GET_CRS():
        return Config.VALUES[Config.CRS]

    def GET_WORKLOADS():
        return Config.VALUES[Config.WORKLOADS]
    
    def GET_METRICS_INFLUXDBS():
        if Config.METRICS_PROVIDERS in Config.VALUES and Config.METRICS_INFLUXDBS in Config.VALUES[Config.METRICS_PROVIDERS]:
            return Config.VALUES[Config.METRICS_PROVIDERS][Config.METRICS_INFLUXDBS]

    def GET_METRICS_REST():
        if Config.METRICS_PROVIDERS in Config.VALUES and Config.METRICS_REST in Config.VALUES[Config.METRICS_PROVIDERS]:
            return Config.VALUES[Config.METRICS_PROVIDERS][Config.METRICS_REST]