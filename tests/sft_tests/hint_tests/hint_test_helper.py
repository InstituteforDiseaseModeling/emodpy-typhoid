import os
import sys
import shutil

from idm_test.dtk_test.integration.integration_test import IntegrationTest
import emod_api.interventions.common as comm
from idmtools.core.platform_factory import Platform

from emodpy.emod_task import EMODTask
from idmtools.entities.experiment import Experiment
from idm_test.dtk_test.integration import manifest

sys.path.append('../')
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from helper import year_to_days, setup

BASE_YEAR = 2005
SIMULATION_DURATION_IN_YEARS = 5
CAMP_START_YEAR = 2006

current_dir = os.path.dirname(__file__)
Age_Bin_Edges_In_Years=[0, 5, 20, 60, -1]
num_age_bin = len(Age_Bin_Edges_In_Years) - 1


def set_param_fn(config):
    """
    Update the config parameters from default values.
    """
    print("Setting params.")
    config.parameters.Simulation_Type = "TYPHOID_SIM"
    config.parameters.Simulation_Duration = SIMULATION_DURATION_IN_YEARS * 365.0
    config.parameters.Base_Individual_Sample_Rate = 0.2

    config.parameters.Base_Year = BASE_YEAR
    config.parameters.Inset_Chart_Reporting_Start_Year = 2005
    config.parameters.Inset_Chart_Reporting_Stop_Year = 2020
    config.parameters.Enable_Demographics_Reporting = 0
    config.parameters.Report_Typhoid_ByAgeAndGender_Start_Year = 2005
    config.parameters.Report_Typhoid_ByAgeAndGender_Stop_Year = 2020

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

    config.parameters.Demographics_Filenames = ["TestDemographics_pak_updated.json"]
    config.parameters.Enable_Property_Output = 0
    config.parameters.Report_Event_Recorder_Events = ["VaccineDistributed", "NewInfectionEvent"]
    config.parameters["Listed_Events"] = ["VaccineDistributed"]  # old school

    config.parameters.Age_Initialization_Distribution_Type = "DISTRIBUTION_COMPLEX"
    config.parameters.Death_Rate_Dependence = "NONDISEASE_MORTALITY_BY_YEAR_AND_AGE_FOR_EACH_GENDER"
    config.parameters.Birth_Rate_Dependence = "INDIVIDUAL_PREGNANCIES_BY_AGE_AND_YEAR"
    # when using 2018 binary
    import emodpy_typhoid.config as config_utils
    config_utils.cleanup_for_2018_mode(config)
    return config


def build_camp():
    import emod_api.campaign as camp

    print(f"Telling emod-api to use {manifest.schema_file} as schema.")
    camp.set_schema(manifest.schema_file)
    import emodpy_typhoid.interventions.outbreak as ob
    ob_event = ob.add_outbreak_individual(start_day=1,
                                          demographic_coverage=0.05,
                                          repetitions=1,
                                          timesteps_between_repetitions=30
                                          )
    camp.add(ob_event)

    def add_historical_vax(camp, ria_coverage=0.75, camp_coverage=0.75, efficacy=0.8, expiration=3650):
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

    # add_historical_vax(camp, ria_coverage=1.0, camp_coverage=1.0, efficacy=1.0, expiration=36500)
    return camp


def build_demog():
    """
    Build a demographics input file for the DTK using emod_api.
    """
    import emodpy_typhoid.demographics.TyphoidDemographics as Demographics  # OK to call into emod-api

    demog = Demographics.from_template_node(lat=0, lon=0, pop=10000, name=1, forced_id=1)
    return demog


def build_demog_target_all_age_bin(value=1):
    """
    Build a demographics input file for the DTK using emod_api with AgeDependentTransmission matrix all set to a
    constant value.
    """
    demog = build_demog()

    demog.AddAgeDependentTransmission(
        Age_Bin_Edges_In_Years=Age_Bin_Edges_In_Years.copy(),
        TransmissionMatrix=[[value] * num_age_bin for _ in range(num_age_bin)]
    )

    return demog


def build_demog_target_one_age_bin(group_index=0, value=1):
    """
    Build a demographics input file for the DTK using emod_api with AgeDependentTransmission matrix. The transmission
    matrix will have a constant value for one group and 0 for the other groups
    """
    demog = build_demog()
    TransmissionMatrix = [[0] * num_age_bin for _ in range(num_age_bin)]

    for row in TransmissionMatrix:
        row[group_index] = value

    demog.AddAgeDependentTransmission(
        Age_Bin_Edges_In_Years=Age_Bin_Edges_In_Years.copy(),
        TransmissionMatrix=TransmissionMatrix
    )

    return demog


class TestAgeBaseHint(IntegrationTest):
    """
    Base test class for Age Base HINT test, that inherits the IntegrationTest class from
    dm_test.dtk_test.integration.integration_test.
    Each new test class will call the age_base_hint_test() function to perform the test.
    """
    def setUp(self):
        self.test_name = self.case_name = str(self.test_name) + "--" + self._testMethodName
        self.platform = Platform("SLURM2", priority="Normal")
        setup(self.platform)

    def tearDown(self) -> None:
        exp_folder = self.experiment.id
        if os.path.exists(exp_folder) and os.path.isdir(exp_folder):
            shutil.rmtree(exp_folder, ignore_errors=True)

    def age_base_hint_test(self, custom_build_demog):
        task = EMODTask.from_default2(config_path="config.json", eradication_path=manifest.eradication_path,
                                      campaign_builder=build_camp, demog_builder=custom_build_demog,
                                      schema_path=manifest.schema_file, param_custom_cb=set_param_fn,
                                      ep4_custom_cb=self._add_ep4)

        task.common_assets.add_directory(os.path.join("..", "..", "Assets"))
        task.config.parameters.Demographics_Filenames = ["demographics.json", "TestDemographics_pak_updated.json"]
        task.set_sif(manifest.sft_id)
        self.experiment = Experiment.from_task(task, name=self.test_name)
        # The last step is to call run() on the ExperimentManager to run the simulations.
        self.experiment.run(wait_until_done=True)
        task.handle_experiment_completion(self.experiment)
        self.experiment = self.experiment
        self._check_result()