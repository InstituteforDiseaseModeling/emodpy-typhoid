import json
import os
import sys
import unittest
from functools import partial
from glob import glob

import numpy
import numpy as np
import pandas as pd
from emodpy.emod_task import EMODTask
import emod_api.campaign as camp
import emod_api.interventions.outbreak as ob
import emodpy_typhoid.interventions.typhoid_vaccine as tv
import emod_api.interventions.common as comm
from idmtools.builders import SimulationBuilder
from idmtools.core import ItemType
from idmtools.core.platform_factory import Platform
from idmtools.entities.experiment import Experiment
import itertools
import pytest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import manifest

BASE_YEAR = 2005
SIMULATION_DURATION_IN_YEARS = 25
CAMP_START_YEAR = 2015


def year_to_days(year):
    return (year - BASE_YEAR) * 365


class TyphoidVaxTests(unittest.TestCase):

    def compare_cases_before_vax(self, a, b):
        a_cases_before_vax = a.loc[a['Time Of Report (Year)'].astype(int) < CAMP_START_YEAR]
        a_list = \
            a_cases_before_vax[['Time Of Report (Year)', 'Newly Infected', "Age"]].groupby(
                ['Time Of Report (Year)', 'Age']).sum()[
                'Newly Infected'].tolist()
        b_cases_before_vax = b.loc[b['Time Of Report (Year)'].astype(int) < CAMP_START_YEAR]
        b_list = \
            b_cases_before_vax[['Time Of Report (Year)', 'Newly Infected', "Age"]].groupby(
                ['Time Of Report (Year)', 'Age']).sum()[
                'Newly Infected'].tolist()
        # validate before vax starts, all simulations has same infected number
        self.assertListEqual(a_list, b_list)

    def compare_cases_after_vax(self, a, b, vax_expiration_year=0):
        if vax_expiration_year != 0:
            a_cases_after_vax = a.loc[
                (a['Time Of Report (Year)'].astype(int) >= CAMP_START_YEAR) & (a['Time Of Report (Year)'].astype(
                    int) <= CAMP_START_YEAR + vax_expiration_year)]
            b_cases_after_vax = b.loc[
                (b['Time Of Report (Year)'].astype(int) >= CAMP_START_YEAR) & (b['Time Of Report (Year)'].astype(
                    int) <= CAMP_START_YEAR + vax_expiration_year)]
        else:
            a_cases_after_vax = a.loc[a['Time Of Report (Year)'].astype(int) >= CAMP_START_YEAR]
            b_cases_after_vax = a.loc[a['Time Of Report (Year)'].astype(int) >= CAMP_START_YEAR]
        a_list = \
            a_cases_after_vax[['Time Of Report (Year)', 'Newly Infected', "Age"]].groupby(
                ['Time Of Report (Year)', 'Age']).mean()[
                'Newly Infected'].tolist()
        # b_cases_after_vax = b.loc[b['Time Of Report (Year)'].astype(int) >= CAMP_START_YEAR]
        b_list = \
            b_cases_after_vax[['Time Of Report (Year)', 'Newly Infected', "Age"]].groupby(
                ['Time Of Report (Year)', 'Age']).mean()[
                'Newly Infected'].tolist()
        self.assertTrue(sum(a_list) >=sum(b_list))

    def compare_cases_after_vax_age_15(self, a, b, vax_expiration_year=0):
        if vax_expiration_year != 0:
            a_cases_after_vax = a.loc[
                (a['Time Of Report (Year)'].astype(int) >= CAMP_START_YEAR) & (a['Time Of Report (Year)'].astype(
                    int) <= CAMP_START_YEAR + vax_expiration_year)]
            b_cases_after_vax = b.loc[
                (b['Time Of Report (Year)'].astype(int) >= CAMP_START_YEAR) & (b['Time Of Report (Year)'].astype(
                    int) <= CAMP_START_YEAR + vax_expiration_year)]
        else:
            a_cases_after_vax = a.loc[a['Time Of Report (Year)'].astype(int) >= CAMP_START_YEAR]
            b_cases_after_vax = b.loc[b['Time Of Report (Year)'].astype(int) >= CAMP_START_YEAR]

        # validate after vax starts, total infected number of age groups from 0-15 from a is always greater than in b's
        first_15_age_groups_cases_a = a_cases_after_vax[['Time Of Report (Year)', 'Newly Infected', "Age"]].groupby(
            ['Time Of Report (Year)', 'Age']).sum().head(15).iloc[:, 0].tolist()
        first_15_age_groups_cases_b = b_cases_after_vax[['Time Of Report (Year)', 'Newly Infected', "Age"]].groupby(
            ['Time Of Report (Year)', 'Age']).sum().head(15).iloc[:, 0].tolist()
        self.assertTrue(sum(first_15_age_groups_cases_a) >= sum(first_15_age_groups_cases_b))

    @classmethod
    def setUpClass(cls) -> None:
        import emod_typhoid.bootstrap as dtk
        dtk.setup(manifest.model_dl_dir)

    def setUp(self):
        # self.platform = Platform("SLURM", priority="Highest", node_group="idm_48cores")
        self.platform = Platform("SLURM2", priority="Normal")
        self.case_name = os.path.basename(__file__) + "--" + self._testMethodName

    def set_param_fn(self, config):
        config.parameters.Simulation_Type = "TYPHOID_SIM"
        config.parameters.Simulation_Duration = SIMULATION_DURATION_IN_YEARS * 365.0
        config.parameters.Base_Individual_Sample_Rate = 0.2

        config.parameters.Base_Year = BASE_YEAR
        config.parameters.Inset_Chart_Reporting_Start_Year = 2005
        config.parameters.Inset_Chart_Reporting_Stop_Year = 2030
        config.parameters.Enable_Demographics_Reporting = 0
        config.parameters.Report_Typhoid_ByAgeAndGender_Start_Year = 2005
        config.parameters.Report_Typhoid_ByAgeAndGender_Stop_Year = 2030
        config.parameters.Demographics_Filenames = [
            "TestDemographics_pak_updated.json"
        ]
        # config.parameters.Enable_Property_Output = 0
        config.parameters.Report_Event_Recorder_Events = ["VaccineDistributed"]
        config.parameters["Listed_Events"] = ["VaccineDistributed"]  # old school

        config.parameters.Age_Initialization_Distribution_Type = "DISTRIBUTION_COMPLEX"
        config.parameters.Death_Rate_Dependence = "NONDISEASE_MORTALITY_BY_YEAR_AND_AGE_FOR_EACH_GENDER"
        config.parameters.Birth_Rate_Dependence = "INDIVIDUAL_PREGNANCIES_BY_AGE_AND_YEAR"
        # when using 2018 binary
        import emodpy_typhoid.config as config_utils
        config_utils.cleanup_for_2018_mode(config)
        return config

    def update_campaign_start(self, simulation, value):
        build_campaign_partial = partial(self.build_camp, start_day=value)
        simulation.task.create_campaign_from_callback(build_campaign_partial)
        return {"campaign_start_day": value}

    def update_campaign_efficacy(self, build_camp, simulation, value):
        build_campaign_partial = partial(build_camp, vax_eff=value)
        simulation.task.create_campaign_from_callback(build_campaign_partial)
        return {"vax_efficacy": value}

    def update_campaign_coverage(self, build_camp, simulation, value):
        build_campaign_partial = partial(build_camp, coverage=value)
        simulation.task.create_campaign_from_callback(build_campaign_partial)
        return {"Demographic Coverage": value}

    def update_campaign_decay(self, build_camp, simulation, value):
        build_campaign_partial = partial(build_camp, decay_constant=value)
        simulation.task.create_campaign_from_callback(build_campaign_partial)
        return {"Decay_Time_Constant": value}

    def update_sim_random_seed(self, simulation, value):
        simulation.task.config.parameters.Run_Number = value
        return {"Run_Number": value}

    def get_emod_task(self, set_param_fn):
        numpy.random.seed(0)
        task = EMODTask.from_default2(config_path="config.json", eradication_path=manifest.eradication_path,
                                      campaign_builder=None, demog_builder=None,
                                      schema_path=manifest.schema_file, param_custom_cb=set_param_fn,
                                      ep4_custom_cb=None)

        current_dir = os.path.dirname(__file__)
        task.common_assets.add_asset(os.path.join(current_dir, "../../examples/HINTy/Assets/TestDemographics_pak_updated.json"))
        task.set_sif(manifest.sif)
        return task

    def test_new_routine_immunization_sweep_vax_effs(self):
        vax_expiration_year = 2
        def build_camp(start_day_offset=1, vax_eff=0.82, coverage=1):
            camp.set_schema(manifest.schema_file)

            for x in range(10):
                event = ob.new_intervention(camp, timestep=1 + x, cases=1)
                camp.add(event)

            ria = tv.new_routine_immunization(camp,
                                              efficacy=vax_eff,
                                              start_day=year_to_days(CAMP_START_YEAR) + start_day_offset,
                                              coverage=coverage,
                                              expected_expiration=vax_expiration_year * 365,
                                              decay_constant=0
                                              )
            camp.add(ria)
            return camp

        task = self.get_emod_task(self.set_param_fn)
        builder = SimulationBuilder()
        vax_effs = np.linspace(0, 1.0, 3)  # 0.0, 0.5, 1 (total 3 sims)
        builder.add_sweep_definition(partial(self.update_campaign_efficacy, build_camp), vax_effs)
        # cov = np.linspace(0, 1.0, 3)
        # builder.add_sweep_definition(partial(self.update_campaign_coverage, build_camp), cov)
        builder.add_sweep_definition(self.update_sim_random_seed, range(1))

        experiment = Experiment.from_builder(builder, task, name=self.case_name)
        experiment.run(wait_until_done=True, platform=self.platform)
        # exp_id = "55f5f1db-6e77-ee11-92fd-f0921c167864"
        # experiment = self.platform.get_item(exp_id, item_type=ItemType.EXPERIMENT)
        task.handle_experiment_completion(experiment)
        task.get_file_from_comps(experiment.uid, ["ReportTyphoidByAgeAndGender.csv", "campaign.json"])
        # Get downloaded local ReportEventRecorder.csv file path for all simulations
        reporteventrecorder_downloaded = list(
            glob(os.path.join(experiment.id, "**/ReportTyphoidByAgeAndGender.csv"), recursive=True))
        campaign_downloaded = list(glob(os.path.join(experiment.id, "**/campaign.json"), recursive=True))
        reporteventrecorder_downloaded.sort()
        campaign_downloaded.sort()
        # ---------------------------------------------
        # Test campaign.json
        for i in range(len(campaign_downloaded)):
            with open(campaign_downloaded[i], "r") as content:
                campaign_list = json.loads(content.read())['Events']
                self.assertEqual(len(campaign_list), 11)
                # verify first 10 events are Outbreaks
                for j in range(10):
                    self.assertEqual(
                        campaign_list[j]['Event_Coordinator_Config']['Intervention_Config']['class'], 'Outbreak')
                # verify #11 event is DelayedIntervention with Brith trigger
                camp_intv_config = campaign_list[10]['Event_Coordinator_Config']['Intervention_Config']
                self.assertEqual(camp_intv_config[
                                     'Actual_IndividualIntervention_Config']['Intervention_Name'],
                                 'DelayedIntervention')
                self.assertEqual(camp_intv_config[
                                     'Actual_IndividualIntervention_Config']['Delay_Period_Max'], 277)
                self.assertEqual(camp_intv_config[
                                     'Actual_IndividualIntervention_Config']['Delay_Period_Min'], 263)
                self.assertEqual(
                    camp_intv_config['Actual_IndividualIntervention_Config']['Actual_IndividualIntervention_Configs'][
                        0]['Intervention_Name'], 'SimpleVaccine')
                self.assertEqual(
                    camp_intv_config['Actual_IndividualIntervention_Config']['Actual_IndividualIntervention_Configs'][
                        0]['Vaccine_Type'], 'AcquisitionBlocking')
                self.assertEqual(
                    camp_intv_config['Actual_IndividualIntervention_Config']['Actual_IndividualIntervention_Configs'][
                        0]['Waning_Config']['Expected_Discard_Time'], 730)
                if i == 0:
                    self.assertEqual(
                        camp_intv_config['Actual_IndividualIntervention_Config'][
                            'Actual_IndividualIntervention_Configs'][0]['Waning_Config']['Initial_Effect'], 0.0)
                elif i == 1:
                    self.assertEqual(
                        camp_intv_config['Actual_IndividualIntervention_Config'][
                            'Actual_IndividualIntervention_Configs'][0]['Waning_Config']['Initial_Effect'], 0.5)
                elif i == 2:
                    self.assertEqual(
                        camp_intv_config['Actual_IndividualIntervention_Config'][
                            'Actual_IndividualIntervention_Configs'][0]['Waning_Config']['Initial_Effect'], 1)
        # ---------------------------------------------
        # Test prevalence in ReportTyphoidByAgeAndGender.csv
        infected_by_age = pd.DataFrame()
        df_list = []
        for i in range(len(reporteventrecorder_downloaded)):
            # read ReportEventRecorder.csv from each sim
            df = pd.read_csv(reporteventrecorder_downloaded[i])
            df.columns = df.columns.to_series().apply(lambda x: x.strip())
            df_list.append(df)

        for a, b in itertools.combinations(df_list, 2):
            self.compare_cases_before_vax(a, b)
            self.compare_cases_after_vax(a, b)


    def test_campaign_immunization_sweep_vax_effs(self):
        vax_expiration_year = 2
        def build_camp(start_day_offset=1, vax_eff=0.82, coverage=1):
            camp.set_schema(manifest.schema_file)

            for x in range(10):
                event = ob.new_intervention(camp, timestep=1 + x, cases=1)
                camp.add(event)

            tv_iv = tv.new_vax(camp,
                               efficacy=vax_eff,
                               expected_expiration=vax_expiration_year * 365
                               )
            one_time_campaign = comm.ScheduledCampaignEvent(camp,
                                                            Start_Day=year_to_days(CAMP_START_YEAR) + start_day_offset,
                                                            Intervention_List=[tv_iv],
                                                            Demographic_Coverage=coverage,
                                                            Target_Age_Min=0.75,
                                                            Target_Age_Max=15,
                                                            )
            camp.add(one_time_campaign)

            return camp

        task = self.get_emod_task(self.set_param_fn)
        builder = SimulationBuilder()
        vax_effs = np.linspace(0, 1.0, 3)  # 0.0, 0.5, 1 (total 3 sims)
        builder.add_sweep_definition(partial(self.update_campaign_efficacy, build_camp), vax_effs)
        builder.add_sweep_definition(self.update_sim_random_seed, range(1))
        experiment = Experiment.from_builder(builder, task, name=self.case_name)
        experiment.run(wait_until_done=True, platform=self.platform)

        task.handle_experiment_completion(experiment)
        # Get downloaded local ReportEventRecorder.csv file path for all simulations
        task.get_file_from_comps(experiment.uid, ["ReportTyphoidByAgeAndGender.csv", "campaign.json"])
        reporteventrecorder_downloaded = list(
            glob(os.path.join(experiment.id, "**/ReportTyphoidByAgeAndGender.csv"), recursive=True))
        campaign_downloaded = list(glob(os.path.join(experiment.id, "**/campaign.json"), recursive=True))
        reporteventrecorder_downloaded.sort()
        campaign_downloaded.sort()
        # ---------------------------------------------
        # Test campaign.json
        for i in range(len(campaign_downloaded)):
            with open(campaign_downloaded[i], "r") as content:
                campaign_list = json.loads(content.read())['Events']
                self.assertEqual(len(campaign_list), 11)
                # verify first 10 events are Outbreaks
                for j in range(10):
                    self.assertEqual(
                        campaign_list[j]['Event_Coordinator_Config']['Intervention_Config']['class'], 'Outbreak')
                # verify #11 event is DelayedIntervention with Birth trigger
                camp_intv_config = campaign_list[10]['Event_Coordinator_Config']['Intervention_Config']
                self.assertEqual(camp_intv_config['Intervention_Name'], 'SimpleVaccine')
                self.assertEqual(camp_intv_config['Vaccine_Type'], 'AcquisitionBlocking')
                self.assertEqual(
                    campaign_list[10]['Event_Coordinator_Config']['Target_Age_Max'], 15)
                self.assertEqual(
                    campaign_list[10]['Event_Coordinator_Config']['Target_Age_Min'], 0.75)
                self.assertEqual(
                    campaign_list[10]['Event_Coordinator_Config']['Demographic_Coverage'], 1)

        # ---------------------------------------------
        # Test prevalence in ReportTyphoidByAgeAndGender.csv
        infected_by_age = pd.DataFrame()
        df_list = []
        for i in range(len(reporteventrecorder_downloaded)):
            # read ReportEventRecorder.csv from each sim
            df = pd.read_csv(reporteventrecorder_downloaded[i])
            df.columns = df.columns.to_series().apply(lambda x: x.strip())
            df_list.append(df)

        for a, b in itertools.combinations(df_list, 2):
            self.compare_cases_before_vax(a, b)
            self.compare_cases_after_vax_age_15(a,b, vax_expiration_year=vax_expiration_year)

    def test_campaign_immunization_sweep_coverage(self):
        vax_expiration_year = 2

        def build_camp(start_day_offset=1, vax_eff=0.82, coverage=1):
            camp.set_schema(manifest.schema_file)

            for x in range(10):
                event = ob.new_intervention(camp, timestep=1 + x, cases=1)
                camp.add(event)

            tv_iv = tv.new_vax(camp,
                               efficacy=vax_eff,
                               expected_expiration=vax_expiration_year * 365
                               )
            one_time_campaign = comm.ScheduledCampaignEvent(camp,
                                                            Start_Day=year_to_days(CAMP_START_YEAR) + start_day_offset,
                                                            Intervention_List=[tv_iv],
                                                            Demographic_Coverage=coverage,
                                                            Target_Age_Min=0.75,
                                                            Target_Age_Max=15
                                                            )
            camp.add(one_time_campaign)

            return camp

        task = self.get_emod_task(self.set_param_fn)
        builder = SimulationBuilder()
        # vax_effs = np.linspace(0, 1.0, 3)  # 0.0, 0.5, 1 (total 3 sims)
        # builder.add_sweep_definition(partial(self.update_campaign_efficacy, build_camp), vax_effs)
        cov = np.linspace(0, 1.0, 3)
        builder.add_sweep_definition(partial(self.update_campaign_coverage, build_camp), cov)
        builder.add_sweep_definition(self.update_sim_random_seed, range(1))
        experiment = Experiment.from_builder(builder, task, name=self.case_name)
        experiment.run(wait_until_done=True, platform=self.platform)
        #exp_id = 'dd4fd81b-5f77-ee11-92fd-f0921c167864'
        #experiment = self.platform.get_item(exp_id, item_type=ItemType.EXPERIMENT)
        task.handle_experiment_completion(experiment)
        task.get_file_from_comps(experiment.uid, ["ReportTyphoidByAgeAndGender.csv", "campaign.json"])
        reporteventrecorder_downloaded = list(
            glob(os.path.join(experiment.id, "**/ReportTyphoidByAgeAndGender.csv"), recursive=True))
        campaign_downloaded = list(glob(os.path.join(experiment.id, "**/campaign.json"), recursive=True))
        reporteventrecorder_downloaded.sort()
        campaign_downloaded.sort()
        # ---------------------------------------------
        # Test campaign.json
        for i in range(len(campaign_downloaded)):
            with open(campaign_downloaded[i], "r") as content:
                campaign_list = json.loads(content.read())['Events']
                self.assertEqual(len(campaign_list), 11)
                # verify coverage
                self.assertEqual(
                    campaign_list[10]['Event_Coordinator_Config']['Demographic_Coverage'], cov[i])
        df_list = []
        for i in range(len(reporteventrecorder_downloaded)):
            # read ReportEventRecorder.csv from each sim
            df = pd.read_csv(reporteventrecorder_downloaded[i])
            df.columns = df.columns.to_series().apply(lambda x: x.strip())
            df_list.append(df)

        # compare cases after vax with duration of expected_expiration_year for all simulations
        for a, b in itertools.combinations(df_list, 2):
           self.compare_cases_after_vax(a, b, vax_expiration_year=vax_expiration_year)

    def test_campaign_immunization_sweep_decay_time_constant(self):
        def build_camp(start_day_offset=1, vax_eff=0.82, decay_constant=6935, coverage=1):
            camp.set_schema(manifest.schema_file)

            for x in range(10):
                event = ob.new_intervention(camp, timestep=1 + x, cases=1)
                camp.add(event)

            tv_iv = tv.new_vax(camp,
                               efficacy=vax_eff,
                               decay_constant=decay_constant
                               )
            one_time_campaign = comm.ScheduledCampaignEvent(camp,
                                                            Start_Day=year_to_days(CAMP_START_YEAR) + start_day_offset,
                                                            Intervention_List=[tv_iv],
                                                            Demographic_Coverage=coverage,
                                                            Target_Age_Min=0.75,
                                                            Target_Age_Max=15
                                                            )
            camp.add(one_time_campaign)

            return camp

        task = self.get_emod_task(self.set_param_fn)
        builder = SimulationBuilder()
        decay_constant = [1000, 2000, 3000]
        builder.add_sweep_definition(partial(self.update_campaign_decay, build_camp), decay_constant)
        builder.add_sweep_definition(self.update_sim_random_seed, range(1))
        experiment = Experiment.from_builder(builder, task, name=self.case_name)
        experiment.run(wait_until_done=True, platform=self.platform)
        # exp_id = 'fb4df8ca-6f77-ee11-92fd-f0921c167864'
        # experiment = self.platform.get_item(exp_id, item_type=ItemType.EXPERIMENT)
        task.handle_experiment_completion(experiment)
        task.get_file_from_comps(experiment.uid, ["ReportTyphoidByAgeAndGender.csv", "campaign.json"])
        reporteventrecorder_downloaded = list(
            glob(os.path.join(experiment.id, "**/ReportTyphoidByAgeAndGender.csv"), recursive=True))
        campaign_downloaded = list(glob(os.path.join(experiment.id, "**/campaign.json"), recursive=True))
        reporteventrecorder_downloaded.sort()
        campaign_downloaded.sort()
        # ---------------------------------------------
        # Test campaign.json
        for i in range(len(campaign_downloaded)):
            with open(campaign_downloaded[i], "r") as content:
                campaign_list = json.loads(content.read())['Events']
                self.assertEqual(len(campaign_list), 11)
                camp_intv_config = campaign_list[10]['Event_Coordinator_Config']['Intervention_Config']
                # verify coverage
                self.assertEqual(camp_intv_config['Waning_Config']['Decay_Time_Constant'], decay_constant[i])
        df_list = []
        for i in range(len(reporteventrecorder_downloaded)):
            # read ReportEventRecorder.csv from each sim
            df = pd.read_csv(reporteventrecorder_downloaded[i])
            df.columns = df.columns.to_series().apply(lambda x: x.strip())
            df_list.append(df)
        for a, b in itertools.combinations(df_list, 2):
            self.compare_cases_before_vax(a, b)
            self.compare_cases_after_vax(a, b)
