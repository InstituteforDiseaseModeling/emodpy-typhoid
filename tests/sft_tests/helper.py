import os
from functools import partial

from idm_test.dtk_test.integration import manifest
from idmtools.assets import Asset
from idmtools.builders import SimulationBuilder

from emodpy_typhoid.utility.sweeping import ItvFn, set_param, sweep_functions

BASE_YEAR = 2005


def year_to_days(year):
    return (year - BASE_YEAR) * 365


def update_sim_random_seed(simulation, value):
    simulation.task.config.parameters.Run_Number = value
    return {"Run_Number": value}


def build_camp():
    """
    Build a campaign input file for the DTK using emod_api.
    Right now this function creates the file and returns the filename. If calling code just needs an asset that's fine.
    """
    import emod_api.campaign as camp

    print(f"Telling emod-api to use {manifest.schema_file} as schema.")
    camp.set_schema(manifest.schema_file)
    import emod_api.interventions.outbreak as ob
    ob.seed(camp, Start_Day=1, Coverage=0.5, Honor_Immunity=False)
    ob.seed(camp, Start_Day=365, Coverage=0.005, Tot_Rep=10, Rep_Interval=30, Honor_Immunity=False)
    return camp


def get_sweep_builders(sweep_list, add_vax_intervention):
    """
    Build simulation builders.
    Args:
        kwargs: User inputs may overwrite the entries in the block.

    Returns:
        lis of Simulation builders
    """
    builder = SimulationBuilder()
    funcs_list = [[
        ItvFn(add_vax_intervention, ce),
        partial(set_param, param='Run_Number', value=x),
    ]
        for ce in sweep_list  # for sweep on sweep_list
        for x in range(2)  # for sweep Run_Number
    ]

    builder.add_sweep_definition(sweep_functions, funcs_list)

    return [builder]


def setup(platform=None):
    manifest.CURRENT_DIR = "."  # do not use this: os.path.abspath(os.path.dirname(__file__))
    import emod_typhoid.bootstrap as dtk
    manifest.SIF_DIR = os.path.join(manifest.CURRENT_DIR, "sif")
    manifest.eradication_path = os.path.join(manifest.SIF_DIR, "Eradication")
    manifest.schema_file = os.path.join(manifest.SIF_DIR, "schema.json")
    manifest.sft_id = os.path.join(os.path.abspath(os.path.dirname(__file__)), "create_sif_with_idm_test",
                                   "SlurmStage_my_shiny_new_idm_test.id")
    manifest.platform = platform
    dtk.setup(manifest.SIF_DIR)
