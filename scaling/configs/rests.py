from scaling.configs.config import Config

class RestConfigs(object):
    """
    methods to extract kahm secret, send kahm event
    """
    kahm_secret_values = None
    NS = ""
    ATTR_URL = "url"
    ATTR_USERNAME = "username"
    ATTR_PASSWORD = "password"
    ATTR_APIS ="apis"
    ATTR_PATH = "path"
    ATTR_METHOD = "method"
    ATTR_SELECTOR = "selector"

    DEFAULT_METHOD = "http"
    TYPE_METHORD_GET = "GET"
    TYPE_METHORD_POST = "POST"

    def LIST():
        configs = dict()
        for cname in Config.GET_METRICS_REST():
            configs[cname] = Config.GET_METRICS_REST()[cname]       
        return configs


    def GET(name):
        if name in Config.GET_METRICS_REST():
            return Config.GET_METRICS_REST()[name]
        return None

    def GET_URL(config):
        if RestConfigs.ATTR_URL in config:
            return config[RestConfigs.ATTR_URL]

    def GET_USERNAME(config):
        if RestConfigs.ATTR_USERNAME in config:
            return config[RestConfigs.ATTR_USERNAME]
    
    def GET_PASSWORD(config):
        if RestConfigs.ATTR_PASSWORD in config:
            return config[RestConfigs.ATTR_PASSWORD]
    
    def GET_API(api, config):
        if RestConfigs.ATTR_APIS in config and api in config[RestConfigs.ATTR_APIS]:
            return config[RestConfigs.ATTR_APIS][api]

    def GET_API_PATH(api, config):
        if RestConfigs.ATTR_APIS in config and api in config[RestConfigs.ATTR_APIS] and RestConfigs.ATTR_PATH in config[RestConfigs.ATTR_APIS][api]:
            return config[RestConfigs.ATTR_APIS][api][RestConfigs.ATTR_PATH]
        else:
            return "/"

    def GET_API_METHOD(api, config):
        if RestConfigs.ATTR_APIS in config and api in config[RestConfigs.ATTR_APIS] and RestConfigs.ATTR_METHOD in config[RestConfigs.ATTR_APIS][api]:
            return config[RestConfigs.ATTR_APIS][api][RestConfigs.ATTR_METHOD]
        else:
            return RestConfigs.DEFAULT_METHOD

    def GET_API_SELECTOR(api, config):
        if RestConfigs.ATTR_APIS in config and api in config[RestConfigs.ATTR_APIS] and RestConfigs.ATTR_SELECTOR in config[RestConfigs.ATTR_APIS][api]:
            return config[RestConfigs.ATTR_APIS][api][RestConfigs.ATTR_SELECTOR]
