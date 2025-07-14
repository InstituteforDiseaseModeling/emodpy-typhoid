#!/usr/bin/env python
import os
import sys

import pandas as pd

from emodpy import emod_task
# idmtools ...
from idmtools.builders import SimulationBuilder
from idmtools.core.platform_factory import Platform
from idmtools.entities.experiment import Experiment
analyzer_path = os.path.join(os.path.dirname(__file__),  "analyzers")
sys.path.insert(0, analyzer_path)
from analyzers.post_processing_with_analysis import post_processing_with_analysis
from analyzers.ssmt_analysis import ssmt_analysis

# emodpy
from emodpy.emod_task import EMODTask
import emodpy.emod_task 
emodpy.emod_task.dev_mode = True

import manifest

def update_sim_bic(simulation, value):
    simulation.task.config.parameters.Base_Infectivity_Constant = value*0.1
    return {"Base_Infectivity": value}

def update_sim_random_seed(simulation, value):
    simulation.task.config.parameters.Run_Number = value
    return {"Run_Number": value}

def set_param_fn( config ):
    config.parameters.Simulation_Type = "TYPHOID_SIM"
    config.parameters.Simulation_Duration = 365.0
    config.parameters.Base_Individual_Sample_Rate = 0.25
    #config.parameters.Enable_Birth = 0 # temporary
    #config.parameters.Minimum_End_Time = 90 
    # cover up for default bugs in schema
    config.parameters.Inset_Chart_Reporting_Start_Year = 1900 
    config.parameters.Inset_Chart_Reporting_Stop_Year = 2050 
    config.parameters.Enable_Demographics_Reporting = 0 
    config.parameters.Node_Contagion_Decay_Rate = 0.33

    # when using 2018 binary
    #config_utils.cleanup_for_2018_mode( config )

    return config


def build_camp():
    """
    Build a campaign input file for the DTK using emod_api. 
    """
    import emod_api.campaign as camp
    import emod_api.interventions.outbreak as ob 

    print(f"Telling emod-api to use {manifest.schema_file} as schema.")
    camp.set_schema( manifest.schema_file )

    event = ob.new_intervention( camp, timestep=1, cases=1 )
    camp.add( event )
    return camp

def build_demog():
    """
    Build a demographics input file for the DTK using emod_api. 
    """
    import emodpy_typhoid.demographics.TyphoidDemographics as Demographics # OK to call into emod-api

    demog = Demographics.from_template_node( lat=0, lon=0, pop=10000, name=1, forced_id=1 )
    wb_births_df = pd.read_csv( manifest.world_bank_dataset )
    demog.SetEquilibriumVitalDynamicsFromWorldBank( wb_births_df=wb_births_df, country='Chile', year=2005 )
    return demog

def include_post_processing(task):
    task = emod_task.add_ep4_from_path(task, manifest.ep4_path)
    return task

def run_test():
    # Create a platform
    # Show how to dynamically set priority and node_group
    platform = Platform("SLURM", node_group="idm_48cores", priority="Highest")

    task = EMODTask.from_default2(config_path="config.json", eradication_path=manifest.eradication_path, campaign_builder=build_camp, demog_builder=build_demog, schema_path=manifest.schema_file, param_custom_cb=set_param_fn, ep4_custom_cb=include_post_processing)

    print("Adding asset dir...")
    task.common_assets.add_directory(assets_directory=manifest.reporters, relative_path="reporter_plugins")

    task.set_sif( manifest.sif )

    # Create simulation sweep with builder
    builder = SimulationBuilder()
    builder.add_sweep_definition( update_sim_random_seed, range(5) )

    # create experiment from builder
    experiment  = Experiment.from_builder(builder, task, name="Typhoid Hello World") 
    # The last step is to call run() on the ExperimentManager to run the simulations.
    experiment.run(wait_until_done=True, platform=platform)

    task.handle_experiment_completion( experiment )

    post_processing_with_analysis(experiment.id)
    ssmt_analysis(experiment.id)


if __name__ == "__main__":
    #dtk.setup( manifest.model_dl_dir )
    
    run_test()
