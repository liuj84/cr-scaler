from scaling.configs.config import Config

class InfluxDBConfigs(object):
    """
    methods to extract kahm secret, send kahm event
    """
    kahm_secret_values = None
    NS = ""

    ATTR_HOST = "host"
    ATTR_PORT = "port"
    ATTR_USERNAME = "username"
    ATTR_PASSWORD = "password"
    ATTR_DATABASE ="database"
    ATTR_QUERY = "query"
    ATTR_QUERIES = "queries"

    def LIST():
        dbs = dict()
        for cname in Config.GET_METRICS_INFLUXDBS():
            dbs[cname] = Config.GET_METRICS_INFLUXDBS()[cname]       
        return dbs


    def GET(name):
        if name in Config.GET_METRICS_INFLUXDBS():
            return Config.GET_METRICS_INFLUXDBS()[name]
        return None

    def GET_HOST(db):
        return db[InfluxDBConfigs.ATTR_HOST]

    def GET_PORT(db):
        return db[InfluxDBConfigs.ATTR_PORT]

    def GET_USERNAME(db):
        return db[InfluxDBConfigs.ATTR_USERNAME]

    def GET_PASSWORD(db):
        return db[InfluxDBConfigs.ATTR_PASSWORD]

    def GET_DATABASE(db):
        return db[InfluxDBConfigs.ATTR_DATABASE]

    def GET_QUERY(query, db):
        return db[InfluxDBConfigs.ATTR_QUERIES][query][InfluxDBConfigs.ATTR_QUERY]

    

