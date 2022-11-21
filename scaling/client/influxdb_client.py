import logging
import sys

from influxdb import InfluxDBClient
from scaling.configs.influxdbs import InfluxDBConfigs
from scaling.utils.constants import Constants

logger = logging.getLogger(Constants.LOGGER)


class InfluxClient(object):

    def __init__(self, ns):
        self.NAMESPACE = ns

    def get_value(self, influx_name, query):
        result = -1
        db = InfluxDBConfigs.GET(influx_name)
        try:
            host=InfluxDBConfigs.GET_HOST(db)
            port=int(InfluxDBConfigs.GET_PORT(db))
            username=InfluxDBConfigs.GET_USERNAME(db)
            password=InfluxDBConfigs.GET_PASSWORD(db)
            database=InfluxDBConfigs.GET_DATABASE(db)
            self.dbclient = InfluxDBClient(host=host, port=port, username=username, password=password, database=database)
            response = self.dbclient.query(InfluxDBConfigs.GET_QUERY(query, db))
        except Exception as e:
            logger.error('get_value: {} failed with error {}'.format(query, e))
            return 0
        if len(response.raw['series']) > 0 and len(response.raw['series'][0]['values']) > 0:
            result = response.raw['series'][0]['values'][0][1]
            logger.debug("get_value response {}, return value {}".format(response, result))
        return result

    

if __name__ == "__main__":
    try:
        client = InfluxClient("default")
        response = client.get_value("pravega", "ss_write_latency")
        print(response)

    except (KeyboardInterrupt, SystemExit):
        print("Exiting")
