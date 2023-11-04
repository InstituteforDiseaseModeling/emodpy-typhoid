import itertools
import os
import shutil
import sys


import numpy as np
from emodpy.emod_task import EMODTask
import emod_api.campaign as camp
from idmtools.entities.experiment import Experiment
from idmtools.entities.templated_simulation import TemplatedSimulations

from idmtools.core.platform_factory import Platform
from idm_test.dtk_test.integration.integration_test import IntegrationTest
from idm_test.dtk_test.integration import manifest
import emod_api.interventions.common as comm

sys.path.append('../..')
from helper import year_to_days, build_camp, get_sweep_builders, setup
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BASE_YEAR = 2005
SIMULATION_DURATION_IN_YEARS = 20
CAMP_START_YEAR = 2015

current_dir = os.path.dirname(__file__)


def set_param_fn(config):
    """
    Update the config parameters from default values.
    """
    print("Setting params.")
    config.parameters.Simulation_Type = "TYPHOID_SIM"
    config.parameters.Simulation_Duration = SIMULATION_DURATION_IN_YEARS * 365.0
    config.parameters.Base_Individual_Sample_Rate = 0.1

    config.parameters.Base_Year = BASE_YEAR
    config.parameters.Inset_Chart_Reporting_Start_Year = 2010
    config.parameters.Inset_Chart_Reporting_Stop_Year = 2020
    config.parameters.Enable_Demographics_Reporting = 0
    config.parameters.Report_Typhoid_ByAgeAndGender_Start_Year = 2010
    config.parameters.Report_Typhoid_ByAgeAndGender_Stop_Year = 2020
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


def add_vax_intervention(campaign, values):
    import emodpy_typhoid.interventions.typhoid_vaccine as tv
    print(f"Telling emod-api to use {manifest.schema_file} as schema.")
    campaign.set_schema(manifest.schema_file)
    tv_iv = tv.new_vax(campaign,
                       efficacy=1,
                       expected_expiration=2190,
                       constant_period=0)
    notification_iv = comm.BroadcastEvent(campaign, "VaccineDistributed")
    one_time_campaign = comm.ScheduledCampaignEvent(camp,
                                                    Start_Day=year_to_days(CAMP_START_YEAR) + 1,
                                                    Intervention_List=[tv_iv, notification_iv],
                                                    Demographic_Coverage=values['coverage'],
                                                    Target_Age_Min=0,
                                                    Target_Age_Max=100
                                                    )
    camp.add(one_time_campaign)
    return {'coverage': values['coverage']}


class TestVaxCampaignCoverage(IntegrationTest):
    def setUp(self):
        self.test_name = self.case_name = os.path.basename(__file__) + "--" + self._testMethodName
        self.platform = Platform("SLURM2", priority="Normal")
        setup(self.platform)

    def tearDown(self) -> None:
        exp_folder = self.experiment.id
        if os.path.exists(exp_folder) and os.path.isdir(exp_folder):
            shutil.rmtree(exp_folder, ignore_errors=True)

    def test_campaign_vax_coverage(self):

        task = EMODTask.from_default2(config_path="config.json", eradication_path=manifest.eradication_path,
                                      campaign_builder=build_camp, demog_builder=None,
                                      schema_path=manifest.schema_file, param_custom_cb=set_param_fn,
                                      ep4_custom_cb=self._add_ep4)

        task.common_assets.add_directory(os.path.join("..", "..", "Assets"))
        task.set_sif(manifest.sft_id)
        cov = np.linspace(start=0.5, stop=1.0, num=6)
        sweep_list = []
        combinations = list(itertools.product(cov))
        for c in combinations:
            sweep_list.append({'coverage': c[0]})
        builders = get_sweep_builders(sweep_list, add_vax_intervention)
        ts = TemplatedSimulations(base_task=task, builders=builders)
        # create experiment from TemplatedSimulations
        self.experiment = Experiment.from_template(ts, name=self.test_name)
        # The last step is to call run() on the ExperimentManager to run the simulations.
        self.experiment.run(wait_until_done=True)
        task.handle_experiment_completion(self.experiment)
        self.experiment = self.experiment
        self._check_result()


if __name__ == '__main__':
    import unittest

    unittest.main()
