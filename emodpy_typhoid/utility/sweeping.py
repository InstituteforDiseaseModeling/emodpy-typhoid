import numpy as np
from typing import Dict, Any, List
from idmtools.entities.simulation import Simulation
from logging import getLogger, DEBUG

logger = getLogger()


##################################################
# Sweeping utility functions
##################################################
def set_param(simulation: Simulation, param: str, value: Any) -> Dict[str, Any]:
    """
    Set specific parameter value.
    Args:
        simulation: idmtools Simulation
        param: parameter
        value: new value

    Returns:
        dict
    """
    # return simulation.task.set_parameter(param, value)

    try:
        return simulation.task.set_parameter(param, value)
    except ValueError:
        if "parameters" in simulation.task.config:
            config = simulation.task.config.parameters
        else:
            config = simulation.task.config

        config[param] = value
        return {param: value}


def sweep_functions(simulation: Simulation, func_list: List) -> Dict[str, Any]:
    """
    Apply funcs on simulation.
    Args:
        simulation: idmtools Simulation
        func_list: a list of functions

    Returns:
        dict of parameters
    """
    tags_updated = {}
    for func in func_list:
        tags = func(simulation)
        if tags:
            tags_updated.update(tags)
    return tags_updated


class ItvFn:
    """
    Sweeping utility: works for sweeping on interventions.
    Requirements:
     - func is a method that takes campaign as first parameter
     - func return a dict

    Returns:
        dict
    """

    def __init__(self, func, *args, **kwargs):
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def __call__(self, simulation: Simulation):
        import emod_api.campaign as campaign
        campaign.reset()

        md = self.func(campaign, *self.args, **self.kwargs)

        # add events
        events = campaign.campaign_dict["Events"]
        simulation.task.campaign.add_events(events)

        # update config for adhoc events
        adhoc_events = campaign.get_adhocs()
        if len(adhoc_events) > 0:
            if logger.isEnabledFor(DEBUG):
                logger.debug("Found adhoc events in campaign. Needs some special processing behind the scenes.")
            if "Custom_Individual_Events" in simulation.task.config.parameters:
                ev_exist = set(simulation.task.config.parameters.Custom_Individual_Events)
                ev_addhoc = set(adhoc_events.keys())
                simulation.task.config.parameters.Custom_Individual_Events = list(ev_exist.union(ev_addhoc))
            else:
                simulation.task.config.parameters.Report_Event_Recorder_Events = list(set(adhoc_events.keys()))
                #pass

        # Make sure we cast numpy types into normal system types
        if md:
            for k, v in md.items():
                if isinstance(v, (np.int64, np.float64, np.float32, np.uint32, np.int16, np.int32)):
                    md[k] = v.item()

        return md


class CfgFn:
    """
    Sweeping utility: works for sweeping on config parameters.
    Requirements:
     - func is a method that takes config as first parameter
     - func return a dict

    Returns:
        dict
    """

    def __init__(self, func, *args, **kwargs):
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def __call__(self, simulation: Simulation):
        md = self.func(simulation.task.config, *self.args, **self.kwargs)

        # Make sure we cast numpy types into normal system types
        if md:
            for k, v in md.items():
                if isinstance(v, (np.int64, np.float64, np.float32, np.uint32, np.int16, np.int32)):
                    md[k] = v.item()

        return md


class SwpFn:
    """
    Sweeping utility: works for sweeping on report, demographics, migrations and climate, etc.
    Requirements:
     - func is a method that takes task as first parameter
     - func return a dict

    Returns:
        dict
    """

    def __init__(self, func, *args, **kwargs):
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def __call__(self, simulation: Simulation):
        md = self.func(simulation.task, *self.args, **self.kwargs)

        # Make sure we cast numpy types into normal system types
        if md:
            for k, v in md.items():
                if isinstance(v, (np.int64, np.float64, np.float32, np.uint32, np.int16, np.int32)):
                    md[k] = v.item()

        return md
