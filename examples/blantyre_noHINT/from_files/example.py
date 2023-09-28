#!/usr/bin/env python

import pandas as pd
import pathlib # for a join
from functools import partial

# idmtools ...
from idmtools.assets import Asset, AssetCollection  #
from idmtools.builders import SimulationBuilder
from idmtools.core.platform_factory import Platform
from idmtools.entities.experiment import Experiment
from idmtools_platform_comps.utils.python_requirements_ac.requirements_to_asset_collection import RequirementsToAssetCollection
from idmtools_models.templated_script_task import get_script_wrapper_unix_task

# emodpy
from emodpy.emod_task import EMODTask
import emodpy.emod_task 

import manifest

sim_idx = 0
def update_sim_random_seed(simulation, value):
    global sim_idx
    sim_idx += 1
    simulation.task.config["Run_Number"] = value
    return {"Run_Number": value, "idx": sim_idx }

def update_sim_param(simulation, value):
    simulation.task.config["Typhoid_Acute_Infectiousness"] = 13435+value
    return {"Typhoid_Acute_Infectiousness": 13435+value}

def run():
    # Create a platform
    # Show how to dynamically set priority and node_group
    platform = Platform("SLURM", node_group="idm_48cores", priority="Highest") 

    task = EMODTask.from_files(config_path="config_feb162019.json", eradication_path=manifest.eradication_path, campaign_path="campaign_feb162019.json", demographics_paths=["TestDemographics_Blantyre.json"], ep4_path=None)


    print("Adding asset dir...")
    task.common_assets.add_directory(assets_directory=manifest.reporters, relative_path="reporter_plugins")

    task.set_sif( manifest.sif )

    # Create simulation sweep with builder
    builder = SimulationBuilder()
    builder.add_sweep_definition( update_sim_random_seed, range(4) )
    builder.add_sweep_definition( update_sim_param, range(4) )

    exp_name = "Typhoid Blantyre NoHINT emodpy from_files"
    # create experiment from builder
    experiment  = Experiment.from_builder(builder, task, name=exp_name ) 
    # The last step is to call run() on the ExperimentManager to run the simulations.
    experiment.run(wait_until_done=True, platform=platform)

    task.handle_experiment_completion( experiment )

    # download and plot some stuff.
    EMODTask.get_file_from_comps( experiment.uid, [ "InsetChart.json" ] )
    task.cache_experiment_metadata_in_sql( experiment.uid, path=exp_name )
    #import emod_api.channelreports.plot_icj_means as plotter
    #chan_data = plotter.collect( "Typhoid Blantyre NoHINT emodpy from_files".replace( " ", "_" ), "Infected" )
    #plotter.display( chan_data, False, "Infected", str( experiment.uid ) )
    

if __name__ == "__main__":
    # Uncomment these two lines just for when you run first time after installing a new emod-typhoid module.
    #import emod_typhoid.bootstrap as dtk
    #dtk.setup( manifest.model_dl_dir )
    run()
