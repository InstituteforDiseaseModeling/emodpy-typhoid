#!/usr/bin/env python
import itertools

import numpy as np  # just for linspace
from functools import partial

# idmtools ...
from idmtools.builders import SimulationBuilder
from idmtools.core import ItemType
from idmtools.core.platform_factory import Platform
from idmtools.entities.experiment import Experiment
from idmtools.entities.templated_simulation import TemplatedSimulations


# emodpy
from emodpy.emod_task import EMODTask

import emod_api.interventions.common as comm

import manifest

from emodpy_typhoid.utility.sweeping import ItvFn, set_param, sweep_functions

BASE_YEAR = 2005
SIMULATION_DURATION_IN_YEARS = 20
CAMP_START_YEAR = 2015


def update_sim_bic(simulation, value):
    simulation.task.config.parameters.Base_Infectivity_Constant = value * 0.1
    return {"Base_Infectivity": value}


def year_to_days(year):
    return ((year - BASE_YEAR) * 365)


def set_param_fn(config):
    config.parameters.Simulation_Type = "TYPHOID_SIM"
    config.parameters.Simulation_Duration = SIMULATION_DURATION_IN_YEARS * 365.0
    config.parameters.Base_Individual_Sample_Rate = 0.2

    config.parameters.Base_Year = BASE_YEAR
    config.parameters.Inset_Chart_Reporting_Start_Year = 2010
    config.parameters.Inset_Chart_Reporting_Stop_Year = 2030
    config.parameters.Enable_Demographics_Reporting = 0
    #config.parameters.Enable_Property_Output = 1  # crash
    config.parameters.Report_Event_Recorder_Events = ["VaccineDistributed", "PropertyChange"]
    config.parameters["Listed_Events"] = ["VaccineDistributed"]  # old school

    config.parameters.Report_Typhoid_ByAgeAndGender_Start_Year = 2010
    config.parameters.Report_Typhoid_ByAgeAndGender_Stop_Year = 2030
    config.parameters.Age_Initialization_Distribution_Type = "DISTRIBUTION_COMPLEX"
    config.parameters.Typhoid_3year_Susceptible_Fraction = 0
    config.parameters.Typhoid_6month_Susceptible_Fraction = 0
    config.parameters.Typhoid_6year_Susceptible_Fraction = 0
    config.parameters.Typhoid_Acute_Infectiousness = 13435
    config.parameters.Typhoid_Carrier_Probability = 0.108
    config.parameters.Typhoid_Carrier_Removal_Year = 2500
    config.parameters.Typhoid_Chronic_Relative_Infectiousness = 0.241
    config.parameters.Typhoid_Contact_Exposure_Rate = 0.06918859049226553
    config.parameters.Typhoid_Environmental_Exposure_Rate = 0.06169346985005757
    config.parameters.Typhoid_Environmental_Cutoff_Days = 157.20690133538764
    config.parameters.Typhoid_Environmental_Peak_Start = 355.0579483941714
    config.parameters.Typhoid_Environmental_Ramp_Down_Duration = 112.30224910440123
    config.parameters.Typhoid_Environmental_Ramp_Up_Duration = 39.540475369174146
    config.parameters.Typhoid_Exposure_Lambda = 7.0
    config.parameters.Typhoid_Prepatent_Relative_Infectiousness = 0.5
    config.parameters.Typhoid_Protection_Per_Infection = 0.98
    config.parameters.Typhoid_Subclinical_Relative_Infectiousness = 1
    config.parameters.Typhoid_Symptomatic_Fraction = 0.07
    # config.parameters.x_Birth = 1.2

    # when using 2018 binary
    import emodpy_typhoid.config as config_utils
    config_utils.cleanup_for_2018_mode(config)
    return config


def build_camp():
    """
    Build a campaign input file for the DTK using emod_api.
    Right now this function creates the file and returns the filename. If calling code just needs an asset that's fine.
    """
    import emod_api.campaign as camp

    print(f"Telling emod-api to use {manifest.schema_file} as schema.")
    camp.set_schema(manifest.schema_file)
    import emodpy_typhoid.interventions.outbreak as ob
    ob_event = ob.add_outbreak_individual(start_day=1,
                                          demographic_coverage=0.25,
                                          node_ids=[1],
                                          repetitions= 5,
                                          timesteps_between_repetitions=1,
                                          ind_property_restrictions=["Region:A"])
    camp.add(ob_event)
    return camp


def build_demog():
    """
    Build a demographics input file for the DTK using emod_api. 
    """
    import emodpy_typhoid.demographics.TyphoidDemographics as Demographics  # OK to call into emod-api

    demog = Demographics.from_template_node(lat=0, lon=0, pop=10000, name=1, forced_id=1)
    # We're getting all our demographics from a static file overlay.

    """
    # This doesn't work right now but still want to leave in example of what we want to be able to do soon.
    demog.AddAgeDependentTransmission( 
            Age_Bin_Edges_In_Years = [0, 5, 20, 60, -1],
            TransmissionMatrix = [
                [1.0, 1.0, 1.0, 1.0],
                [1.0, 1.0, 1.0, 1.0],
                [1.0, 1.0, 1.0, 1.0],
                [1.0, 1.0, 1.0, 1.0]
            ]
    )
    """
    demog.AddIndividualPropertyAndHINT(Property="Region",
                                       Values=["A", "B", "C", "D"],
                                       InitialDistribution=[0.25, 0.25, 0.25, 0.25],
                                       TransmissionMatrix=[
                                           [0.0, 1.0, 2.0, 5.0],
                                           [0.0, 0.0, 0.0, 0.0],
                                           [0.0, 0.0, 0.0, 0.0],
                                           [0.0, 0.0, 0.0, 0.0]
                                       ],
                                       EnviroTransmissionMatrix=[
                                           [0.0, 1.0, 2.0, 5.0],
                                           [0.0, 0.0, 0.0, 0.0],
                                           [0.0, 0.0, 0.0, 0.0],
                                           [0.0, 0.0, 0.0, 0.0]
                                       ]
                                       )
    return demog


def add_vax_intervention(campaign, values):
    import emodpy_typhoid.interventions.typhoid_vaccine as tv
    print(f"Telling emod-api to use {manifest.schema_file} as schema.")
    campaign.set_schema(manifest.schema_file)
    ria = tv.new_routine_immunization(campaign,
                                      efficacy=values['efficacy'],
                                      decay_constant=values['decay_constant'],
                                      start_day=year_to_days(CAMP_START_YEAR) + values['start_day_offset'],
                                      coverage=values['coverage']
                                      )

    notification_iv = comm.BroadcastEvent(campaign, "VaccineDistributed")
    campaign.add(ria)
    #
    tv_iv = tv.new_vax(campaign,
                       efficacy=values['efficacy'],
                       decay_constant=values['decay_constant'],
                       constant_period=0
                       )
    one_time_campaign = comm.ScheduledCampaignEvent(campaign,
                                                    Start_Day=year_to_days(CAMP_START_YEAR) + values['start_day_offset'],
                                                    Intervention_List=[tv_iv, notification_iv],
                                                    Demographic_Coverage=values['coverage'],
                                                    Target_Age_Min=0.75,
                                                    Target_Age_Max=15
                                                    )
    campaign.add(one_time_campaign)
    return {"start_day": values['efficacy'], 'efficacy': values['efficacy'], 'coverage': values['coverage'],
            'decay': values['decay_constant']}


def get_sweep_builders(sweep_list):
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
        for x in range(1)  # for sweep Run_Number
    ]

    builder.add_sweep_definition(sweep_functions, funcs_list)

    return [builder]


def run_test():
    # Create a platform
    # Show how to dynamically set priority and node_group
    platform = Platform("SLURM", node_group="idm_48cores", priority="Highest")

    task = EMODTask.from_default2(config_path="config.json", eradication_path=manifest.eradication_path,
                                  campaign_builder=build_camp, demog_builder=build_demog, schema_path=manifest.schema_file,
                                  param_custom_cb=set_param_fn, ep4_custom_cb=None)
    # normally we don't force-set parameters at this point
    task.config.parameters.Demographics_Filenames = ["demographics.json","TestDemographics_pak_updated.json"]
    task.config.parameters.Death_Rate_Dependence = "NONDISEASE_MORTALITY_BY_YEAR_AND_AGE_FOR_EACH_GENDER"
    task.config.parameters.Birth_Rate_Dependence = "INDIVIDUAL_PREGNANCIES_BY_AGE_AND_YEAR"
    task.common_assets.add_directory(assets_directory=manifest.assets_input_dir)
    task.set_sif(manifest.sif)
    # Create simulation sweep with builder
    start_day_offset = [1]
    vax_effs = np.linspace(0, 1.0, 3)  # 0.0, 0.5, 1.0
    decay = [2000, 3000]
    cov = np.linspace(start=0.5, stop=1.0, num=6)
    sweep_lit = []
    combinations = list(itertools.product(start_day_offset, vax_effs, cov, decay))
    for c in combinations:
        sweep_lit.append({'start_day_offset': c[0], 'efficacy': c[1], 'coverage': c[2], 'decay_constant': c[3]})
    builders = get_sweep_builders(sweep_lit)
    # create TemplatedSimulations from task and builders
    ts = TemplatedSimulations(base_task=task, builders=builders)
    # create experiment from TemplatedSimulations
    experiment = Experiment.from_template(ts, name="test_hint")
    # The last step is to call run() on the ExperimentManager to run the simulations.
    experiment.run(wait_until_done=True, platform=platform)
    # exp_id = '87d7d4eb-3f6a-ee11-92fc-f0921c167864'
    # experiment = platform.get_item(exp_id, item_type=ItemType.EXPERIMENT)
    task.handle_experiment_completion(experiment)

    # download and plot some stuff.
    EMODTask.get_file_from_comps(experiment.uid, ["InsetChart.json", "ReportTyphoidByAgeAndGender.csv"])
    task.cache_experiment_metadata_in_sql(experiment.uid)
    import matplotlib
    matplotlib.use("TkAgg")
    import emod_api.channelreports.plot_icj_means as plotter
    chan_data = plotter.collect(str(experiment.uid), "Infected", tag="efficacy=SWEEP")
    plotter.display(chan_data, False, "Infected", str(experiment.uid))


if __name__ == "__main__":
    import emod_typhoid.bootstrap as dtk

    dtk.setup(manifest.model_dl_dir)

    run_test()
