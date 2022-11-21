import logging
import os
import sys
from jsonpath_ng import jsonpath, parse
import requests
from scaling.utils.constants import Constants
from scaling.configs.rests import RestConfigs

logger = logging.getLogger(Constants.LOGGER)

class RestClient(object):
    def __init__(self, ns):
        self.NAMESPACE = ns
    
    def get_value(self, client_name, api):
        config = RestConfigs.GET(client_name)
        url=RestConfigs.GET_URL(config)
        username=RestConfigs.GET_USERNAME(config)
        password=RestConfigs.GET_PASSWORD(config)
        method=RestConfigs.GET_API_METHOD(api, config)
        api_url = url + RestConfigs.GET_API_PATH(api, config)
        try:
            if method is not None and method.upper() == RestConfigs.TYPE_METHORD_POST:
                if username != "" and username is not None and password != "" and password is not None:
                    response = requests.post(api_url, auth=(username, password))
                else:
                    response = requests.post(api_url)
            else:
                if username != "" and username is not None and password != "" and password is not None:
                    response = requests.get(api_url, auth=(username, password))
                else:
                    response = requests.get(api_url)
        except Exception as e:
            logger.error('get_value: {} failed with error {}'.format(api, e))
            return 0

        resp_json = response.json()
        selector = RestConfigs.GET_API_SELECTOR(api, config)
        agg_method = "sum()" # default aggregation method
        if selector == None or selector == "":
            res = resp_json
        elif selector.endswith('()'):
            jpath = selector[0 : selector.rindex('.')]
            agg_method = selector[selector.rindex('.') + 1 :]
            jsonpath_expr = parse(jpath)
            res = [match.value for match in jsonpath_expr.find(resp_json)]
        else:
            jpath = selector
            jsonpath_expr = parse(jpath)
            res = [match.value for match in jsonpath_expr.find(resp_json)]
        if agg_method == "sum()":
            return sum(res)
        elif agg_method == "avg()" or agg_method == "average()":
            return sum(res) / (len(res) * 1.0)
        elif agg_method == "max()":
            return max(res)
        elif agg_method == "min()":
            return min(res)
        else:
            return sum(res)

if __name__ == "__main__":
    try:
        client = RestClient("default")
        response = client.get_value("pravega", "seg_count")
        print(response)

    except (KeyboardInterrupt, SystemExit):
        print("Exiting")