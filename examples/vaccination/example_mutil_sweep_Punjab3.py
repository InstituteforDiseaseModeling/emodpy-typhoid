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

from emodpy_typhoid.utility.sweeping import ItvFn, set_param, sweep_functions, CfgFn

BASE_YEAR = 1990
SIMULATION_DURATION_IN_YEARS = 40
CAMP_START_YEAR = 2021.169
FWD_CAMP_START_YEAR = 2024.25


def update_sim_bic(simulation, value):
    simulation.task.config.parameters.Base_Infectivity_Constant = value * 0.1
    return {"Base_Infectivity": value}


def year_to_days(year):
    return ((year - BASE_YEAR) * 365)


def set_param_fn(config):
    config.parameters.Simulation_Type = "TYPHOID_SIM"
    config.parameters.Simulation_Duration = SIMULATION_DURATION_IN_YEARS * 365.0
    config.parameters.Base_Individual_Sample_Rate = 1

    config.parameters.Base_Year = BASE_YEAR
    config.parameters.Inset_Chart_Reporting_Start_Year = 1990
    config.parameters.Inset_Chart_Reporting_Stop_Year = 2040
    config.parameters.Enable_Demographics_Reporting = 0
    # config.parameters.Enable_Property_Output = 1
    config.parameters.Report_Event_Recorder_Events = ["VaccineDistributed"]
    config.parameters["Listed_Events"] = ["VaccineDistributed"]  # old school

    config.parameters.Report_Typhoid_ByAgeAndGender_Start_Year = 1990
    config.parameters.Report_Typhoid_ByAgeAndGender_Stop_Year = 2040
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
    # import emod_api.campaign as camp
    #
    # print(f"Telling emod-api to use {manifest.schema_file} as schema.")
    # camp.set_schema(manifest.schema_file)
    # import emod_api.interventions.outbreak as ob
    # for x in range(10):
    #     event = ob.new_intervention(camp, timestep=1 + x, cases=1)
    #     camp.add(event)
    # return camp
    import emod_api.campaign as camp

    print(f"Telling emod-api to use {manifest.schema_file} as schema.")
    camp.set_schema(manifest.schema_file)
    import emod_api.interventions.outbreak as ob
    ob.seed(camp, Start_Day=1, Coverage=0.5, Honor_Immunity=False)
    ob.seed(camp, Start_Day=365, Coverage=0.005, Tot_Rep=10, Rep_Interval=30, Honor_Immunity=False)
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
    return demog


# def add_vax_intervention(campaign, values):
#     import emodpy_typhoid.interventions.typhoid_vaccine as tv
#     print(f"Telling emod-api to use {manifest.schema_file} as schema.")
#     campaign.set_schema(manifest.schema_file)
#     ria = tv.new_routine_immunization(campaign,
#                                       efficacy=values['efficacy'],
#                                       decay_constant=0,
#                                       expected_expiration=values['expected_expiration'],
#                                       start_day=year_to_days(CAMP_START_YEAR) + values['start_day_offset'],
#                                       coverage=values['coverage']
#                                       )
#
#     notification_iv = comm.BroadcastEvent(campaign, "VaccineDistributed")
#     campaign.add(ria)
#     #
#     tv_iv = tv.new_vax(campaign,
#                        efficacy=values['efficacy'],
#                        decay_constant=0,
#                        constant_period=0,
#                        expected_expiration = values['expected_expiration']
#                        )
#     one_time_campaign = comm.ScheduledCampaignEvent(campaign,
#                                                     Start_Day=year_to_days(CAMP_START_YEAR) + values['start_day_offset'],
#                                                     Intervention_List=[tv_iv, notification_iv],
#                                                     Demographic_Coverage=values['coverage'],
#                                                     Target_Age_Min=0.75,
#                                                     Target_Age_Max=15
#                                                     )
#     campaign.add(one_time_campaign)
#     return {"start_day": values['start_day_offset'], 'efficacy': values['efficacy'], 'coverage': values['coverage'],
#             'expected_expiration': values['expected_expiration']}
def add_vax_intervention(campaign, values, min_age=0.75, max_age=15, binary_immunity=True):
    """
    Add 1 or both vaccine interventions:
    1) 'campaign' intervention is a one-time vax to an age-banded segment of the population.
    2) 'ria' intervention is a vax given to infants at 9-months.

    Args:
        campaign: Central campaign builder object.
        values: Dictionary that helps with sweeping, includes 'coverage', 'efficacy', 'decay_constant', and 'start_day_offset'.
        min_age: Minimum age in years for 'campaign'. Can be 0.
        max_age: Maximum age in years for 'campaign'. Can be 125.
        binary_immunity: Vax efficacy can wane continuosly (False) or drop to 0 all at once (True).
    """

    import emodpy_typhoid.interventions.typhoid_vaccine as tv
    print(f"Telling emod-api to use {manifest.schema_file} as schema.")
    campaign.set_schema(manifest.schema_file)
    camp_coverage = values['coverage']

    if binary_immunity:
        tv_iv = tv.new_vax(campaign,
                           efficacy=values['efficacy'],
                           expected_expiration=values['expected_expiration'],
                           constant_period=0)
    else:
        tv_iv = tv.new_vax(campaign,
                           efficacy=values['efficacy'],
                           decay_constant=values['decay_constant'],
                           constant_period=0)

    def add_historical_vax(camp, ria_coverage=0.75, camp_coverage=0.75, efficacy=0.8, expiration=365 * 6):
        import emodpy_typhoid.interventions.typhoid_vaccine as tv

        ria = tv.new_routine_immunization(camp,
                                          efficacy=efficacy,
                                          constant_period=0,
                                          expected_expiration=expiration,
                                          # decay_constant=values['decay_constant'],
                                          start_day=year_to_days(CAMP_START_YEAR),
                                          coverage=ria_coverage)
        tv_iv = tv.new_vax(camp,
                           efficacy=efficacy,
                           expected_expiration=expiration,
                           # decay_constant=values['decay_constant'],
                           constant_period=0)

        notification_iv = comm.BroadcastEvent(camp, "VaccineDistributed")
        camp.add(ria)

        one_time_campaign = comm.ScheduledCampaignEvent(camp,
                                                        Start_Day=year_to_days(CAMP_START_YEAR),
                                                        Intervention_List=[tv_iv, notification_iv],
                                                        Demographic_Coverage=camp_coverage,
                                                        Target_Age_Min=0.75,
                                                        Target_Age_Max=15
                                                        )
        camp.add(one_time_campaign)

    # add_historical_vax( camp )
    add_historical_vax(campaign, ria_coverage=0.75, camp_coverage=camp_coverage, efficacy=values['efficacy'],
                       expiration=365 * 6)

    notification_iv = comm.BroadcastEvent(campaign, "VaccineDistributed")
    one_time_campaign = comm.ScheduledCampaignEvent(campaign,
                                                    Start_Day=year_to_days(FWD_CAMP_START_YEAR),
                                                    Intervention_List=[tv_iv, notification_iv],
                                                    Demographic_Coverage=camp_coverage,
                                                    Target_Age_Min=min_age,
                                                    Target_Age_Max=125
                                                    )
    campaign.add(one_time_campaign)
    return {
        "start_day": values['start_day_offset'],
        'efficacy': values['efficacy'],
        'coverage_camp': camp_coverage,
        'expected_expiration': values['expected_expiration']
    }


def sweep_config_func(config, values):
    config.parameters.Typhoid_Acute_Infectiousness = values['Typhoid_Acute_Infectiousness']
    config.parameters.Typhoid_Exposure_Lambda = values['Typhoid_Exposure_Lambda']
    config.parameters.Typhoid_Environmental_Exposure_Rate = values['Typhoid_Environmental_Exposure_Rate']
    config.parameters.Typhoid_Contact_Exposure_Rate = values['Typhoid_Contact_Exposure_Rate']
    config.parameters.Typhoid_Symptomatic_Fraction = values['Typhoid_Symptomatic_Fraction']
    return {'Typhoid_Acute_Infectiousness': values['Typhoid_Acute_Infectiousness'],
            'Typhoid_Exposure_Lambda': values['Typhoid_Exposure_Lambda'],
            'Typhoid_Environmental_Exposure_Rate': values['Typhoid_Environmental_Exposure_Rate'],
            'Typhoid_Contact_Exposure_Rate': values['Typhoid_Contact_Exposure_Rate'],
            'Typhoid_Symptomatic_Fraction': values['Typhoid_Symptomatic_Fraction']}


def get_sweep_builders(sweep_list, sweep_config):
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
        CfgFn(sweep_config_func, y)
    ]
        for ce in sweep_list  # for sweep on sweep_list
        for x in range(1)  # for sweep Run_Number
        for y in sweep_config
    ]

    builder.add_sweep_definition(sweep_functions, funcs_list)

    return [builder]


def run_test():
    # Create a platform
    # Show how to dynamically set priority and node_group
    platform = Platform("SLURM", node_group="idm_48cores", priority="Highest")

    task = EMODTask.from_default2(config_path="config.json", eradication_path=manifest.eradication_path,
                                  campaign_builder=build_camp, demog_builder=None, schema_path=manifest.schema_file,
                                  param_custom_cb=set_param_fn, ep4_custom_cb=None)
    # normally we don't force-set parameters at this point
    task.config.parameters.Demographics_Filenames = ["TestDemographics_pak_updated.json"]
    task.config.parameters.Death_Rate_Dependence = "NONDISEASE_MORTALITY_BY_YEAR_AND_AGE_FOR_EACH_GENDER"
    task.config.parameters.Birth_Rate_Dependence = "INDIVIDUAL_PREGNANCIES_BY_AGE_AND_YEAR"
    task.common_assets.add_directory(assets_directory=manifest.assets_input_dir)
    task.set_sif(manifest.sif)
    # Create simulation sweep with builder
    start_day_offset = [1]
    vax_effs = [0.9]
    expected_expiration = [2*365, 4*365, 6*365]
    cov = [0.75]
    sweep_list = []
    Typhoid_Acute_Infectiousness = [13000]
    Typhoid_Exposure_Lambda = [5]
    Typhoid_Environmental_Exposure_Rate = [0.4]
    Typhoid_Contact_Exposure_Rate = [0.009]
    min_value = 0.05
    max_value = 0.5
    step = 0.05
    my_array = np.linspace(min_value, max_value, num=int((max_value - min_value) / step) + 1)

    Typhoid_Symptomatic_Fraction = [0.06]
    sweep_config = []
    combinations_config = list(
        itertools.product(Typhoid_Acute_Infectiousness, Typhoid_Exposure_Lambda, Typhoid_Environmental_Exposure_Rate,
                          Typhoid_Contact_Exposure_Rate, Typhoid_Symptomatic_Fraction))

    for c in combinations_config:
        sweep_config.append({'Typhoid_Acute_Infectiousness': c[0], 'Typhoid_Exposure_Lambda': c[1],
                             'Typhoid_Environmental_Exposure_Rate': c[2], 'Typhoid_Contact_Exposure_Rate': c[3],
                             'Typhoid_Symptomatic_Fraction': c[4]})

    combinations = list(itertools.product(start_day_offset, vax_effs, cov, expected_expiration))
    for c in combinations:
        sweep_list.append({'start_day_offset': c[0], 'efficacy': c[1], 'coverage': c[2], 'expected_expiration': c[3]})
    builders = get_sweep_builders(sweep_list, sweep_config)
    # create TemplatedSimulations from task and builders
    ts = TemplatedSimulations(base_task=task, builders=builders)
    # create experiment from TemplatedSimulations
    experiment = Experiment.from_template(ts, name="test_vax_sweep_configs_Punjab_case3")
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
