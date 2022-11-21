from scaling.configs.config import Config

class Workloads(object):
    """
    methods to extract kahm secret, send kahm event
    """
    kahm_secret_values = None
    NS = ""

    # attribute names
    ATTR_COMPONENTS = "components"
    ATTR_REPLICAS = "replicas"
    ATTR_MIN_REPLICAS = "min_replicas"
    ATTR_CONTAINER_NAME = "container_name"
    ATTR_TYPE ="type"
    ATTR_SELECTOR = "selector"
    ATTR_STATUS_CHECKER = "status_checker"
    ATTR_STATUS_CHECKER_PATH = "path"
    ATTR_STATUS_CHECKER_VALUE = "value"

    def LIST():
            workloads = dict()
            for cname in Config.GET_WORKLOADS():
                component = Config.GET_WORKLOADS()[cname]
                # sub component
                if Workloads.ATTR_COMPONENTS in component:
                    sub = component[Workloads.ATTR_COMPONENTS]
                    for workload in sub:
                        workloads[cname + "." + workload] = sub[workload]
                else:
                    workloads[cname] = component
            return workloads
    
    def GET(name):
        if name in Config.GET_WORKLOADS():
            return Config.GET_WORKLOADS()[name]
        if len(name.split('.')) < 2:
            return None
        cname = name.split(".")[0]
        subname = name.split(".")[1]
        component = Config.GET_WORKLOADS()[cname]
        sub = component[Workloads.ATTR_COMPONENTS][subname]
        return sub

    def LIST_WORKLOAD_NAMES():
        return list(Workloads.LIST().keys())

    def GET_WORKLOAD_ATTR(attribute, workload_name = None):
        if workload_name:
            return Workloads.GET(workload_name)[attribute]
        ret = dict()
        workloads = Workloads.LIST()
        for name in workloads:
            ret[name] = workloads[name][attribute]
        return ret
       
    def GET_WORKLOAD_REPLICAS_PATH(workload_name = None):
        return Workloads.GET_WORKLOAD_ATTR(Workloads.ATTR_REPLICAS, workload_name)

    def GET_WORKLOAD_SELECTOR(workload_name = None):
        return Workloads.GET_WORKLOAD_ATTR(Workloads.ATTR_SELECTOR, workload_name)

    def GET_WORKLOAD_TYPE(workload_name = None):
        return Workloads.GET_WORKLOAD_ATTR(Workloads.ATTR_TYPE, workload_name)

    def GET_WORKLOAD_MIN_REPLICAS(workload_name = None):
        return Workloads.GET_WORKLOAD_ATTR(Workloads.ATTR_MIN_REPLICAS, workload_name)

    def GET_WORKLOAD_CONTAINER_NAME(workload_name = None):
        return Workloads.GET_WORKLOAD_ATTR(Workloads.ATTR_CONTAINER_NAME, workload_name)

    def GET_WORKLOAD_STATUS_CHECKER(workload_name = None):
        return Workloads.GET_WORKLOAD_ATTR(Workloads.ATTR_STATUS_CHECKER, workload_name)
