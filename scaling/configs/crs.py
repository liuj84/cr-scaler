from scaling.configs.config import Config

class CRs(object):
    """
    methods to extract kahm secret, send kahm event
    """
    kahm_secret_values = None
    NS = ""

    GROUP = "group"
    VERSION = "version"
    PLURAL = "plural"
    NAME = "name"

    def LIST():
        crs = dict()
        for cname in Config.GET_CRS():
            crs[cname] = Config.GET_CRS()[cname]
            
        return crs
    
    def GET_MAIN_CR_NAME():
        return list(Config.GET_CRS().keys())[0]

    def GET(name):
        if name in Config.GET_CRS():
            return Config.GET_CRS()[name]
        return None

