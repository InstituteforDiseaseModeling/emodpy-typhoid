import json
import os
import pathlib
import unittest
from functools import partial
from glob import glob

import numpy as np
import pandas as pd
from emodpy.emod_task import EMODTask
from idmtools.builders import SimulationBuilder
from idmtools.core import ItemType
from idmtools.core.platform_factory import Platform
from idmtools.entities.experiment import Experiment
import pytest
import manifest

manifest.n_sims = 1
BASE_YEAR = 2010
SIMULATION_DURATION_IN_YEARS = 12
CAMP_START_YEAR = 2019


def update_sim_random_seed(simulation, value):
    simulation.task.config.parameters.Run_Number = value
    return {"Run_Number": value}


def update_sim_bic(simulation, value):
    simulation.task.config.parameters.Base_Infectivity_Constant = value * 0.1
    return {"Base_Infectivity": value}


def year_to_days(year):
    return ((year - BASE_YEAR) * 365)

def find_first(this_list):
    for idx in range(len(this_list)):
        if this_list[idx] > 0:
            return idx
    return len(this_list)

def set_param_fn(config):
    """
    Update the config parameters from default values.
    """
    print("Setting params.")
    config.parameters.Simulation_Type = "TYPHOID_SIM"
    config.parameters.Simulation_Duration = SIMULATION_DURATION_IN_YEARS * 365.0
    config.parameters.Base_Individual_Sample_Rate = 1

    config.parameters.Base_Year = BASE_YEAR
    config.parameters.Inset_Chart_Reporting_Start_Year = 2010
    config.parameters.Inset_Chart_Reporting_Stop_Year = 2030
    config.parameters.Enable_Demographics_Reporting = 0
    config.parameters.Enable_Property_Output = 1
    config.parameters.Report_Event_Recorder_Events = ["VaccineDistributed", "PropertyChange"]
    config.parameters["Listed_Events"] = ["VaccineDistributed"]  # old school
    # config.parameters.Typhoid_Immunity_Memory = 36500
    # config.parameters.Config_Name = "149_Typhoid"
    config.parameters.Age_Initialization_Distribution_Type = "DISTRIBUTION_COMPLEX"
    config.parameters.Report_Typhoid_ByAgeAndGender_Start_Year = 2010
    config.parameters.Report_Typhoid_ByAgeAndGender_Stop_Year = 2030
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

    return config


def build_camp(ip_restrictions=[]):
    """
    Build a campaign input file for the DTK using emod_api.
    Right now this function creates the file and returns the filename. If calling code just needs an asset that's fine.
    """
    import emod_api.campaign as camp

    print(f"Telling emod-api to use {manifest.schema_file} as schema.")
    camp.set_schema(manifest.schema_file)
    import emodpy_typhoid.interventions.outbreak as ob
    import emod_api.interventions.common as comm
    ob_event = ob.add_outbreak_individual(start_day=1,
                                          demographic_coverage=0.5,
                                          node_ids=[1],
                                          repetitions=1,
                                          timesteps_between_repetitions=-1,
                                          ind_property_restrictions=ip_restrictions)
    camp.add(ob_event)
    import emodpy_typhoid.interventions.typhoid_vaccine as tv
    ria = tv.new_routine_immunization(camp,
                                      efficacy=0.85,
                                      start_day=year_to_days(CAMP_START_YEAR) + 1
                                      )

    notification_iv = comm.BroadcastEvent(camp, "VaccineDistributed")
    camp.add(ria)
    #
    tv_iv = tv.new_vax(camp,
                       efficacy=0.82,
                       decay_constant=6935,
                       constant_period=0
                       )
    one_time_campaign = comm.ScheduledCampaignEvent(camp,
                                                    Start_Day=year_to_days(CAMP_START_YEAR) + 1,
                                                    Intervention_List=[tv_iv, notification_iv],
                                                    Demographic_Coverage=0.5,
                                                    Target_Age_Min=0.75,
                                                    Target_Age_Max=15
                                                    )
    camp.add(one_time_campaign)

    return camp


class MultiRouteHINTTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        import emod_typhoid.bootstrap as dtk
        dtk.setup(manifest.model_dl_dir)

    def setUp(self):
        self.platform = Platform("SLURM2", node_group="idm_48cores", priority="Highest")
        self.case_name = os.path.basename(__file__) + "--" + self._testMethodName

    def tearDown(self) -> None:
        file_to_rem = pathlib.Path(self._testMethodName + ".json")
        file_to_rem.unlink(missing_ok=True)

    def update_campaign_ip(self, simulation, value):
        build_campaign_partial = partial(build_camp, ip_restrictions=value)
        simulation.task.create_campaign_from_callback(build_campaign_partial)
        return {"ip_restrictions": value}

    # This test to test transmission between groups
    def test_multiple_route_hint(self):
        def build_demog():
            import emodpy_typhoid.demographics.TyphoidDemographics as Demographics  # OK to call into emod-api

            demog = Demographics.from_template_node(lat=0, lon=0, pop=10000, name=1, forced_id=1)

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
            demog.generate_file(self._testMethodName + ".json")
            return demog

        task = EMODTask.from_default2(
            eradication_path=manifest.eradication_path,
            campaign_builder=build_camp,
            demog_builder=build_demog,
            schema_path=manifest.schema_file,
            param_custom_cb=set_param_fn,
            ep4_custom_cb=None)

        print("Adding asset dir...")
        task.common_assets.add_directory(assets_directory=manifest.assets_input_dir)
        task.common_assets.add_asset(self._testMethodName + ".json")
        task.config.parameters.Demographics_Filenames = [self._testMethodName + ".json",
                                                         "TestDemographics_pak_updated.json"]
        task.config.parameters.Death_Rate_Dependence = "NONDISEASE_MORTALITY_BY_YEAR_AND_AGE_FOR_EACH_GENDER"
        task.config.parameters.Birth_Rate_Dependence = "INDIVIDUAL_PREGNANCIES_BY_AGE_AND_YEAR"
        task.config.parameters["Listed_Events"] = ["VaccineDistributed"]

        task.set_sif(manifest.sif)

        # Create simulation sweep with builder
        builder = SimulationBuilder()
        builder.add_sweep_definition(update_sim_random_seed, range(3))
        builder.add_sweep_definition(self.update_campaign_ip, ['Region:A'])
        # create experiment from builder
        experiment = Experiment.from_builder(builder, task, name=self.case_name)
        # The last step is to call run() on the ExperimentManager to run the simulations.
        experiment.run(wait_until_done=True, platform=self.platform)
        #exp_id = 'd2d7fe69-f267-ee11-92fc-f0921c167864'
        #experiment = self.platform.get_item(exp_id, item_type=ItemType.EXPERIMENT)
        task.handle_experiment_completion(experiment)
        task.get_file_from_comps(experiment.uid, ["PropertyReportTyphoid.json", "ReportTyphoidByAgeAndGender.csv"])
        # Get downloaded local ReportEventRecorder.csv file path for all simulations
        reportbyageandgender_downloaded = list(
            glob(os.path.join(experiment.id, "**/ReportTyphoidByAgeAndGender.csv"), recursive=True))
        propertyreport_downloaded = list(
            glob(os.path.join(experiment.id, "**/PropertyReportTyphoid.json"), recursive=True))
        reportbyageandgender_downloaded.sort()
        propertyreport_downloaded.sort()
        for i in range(len(reportbyageandgender_downloaded)):
            # read ReportEventRecorder.csv from each sim
            df = pd.read_csv(reportbyageandgender_downloaded[i])

            df.columns = df.columns.to_series().apply(lambda x: x.strip())
            with open(propertyreport_downloaded[i], "r") as content:
                property_list = json.loads(content.read())
            #df_pr.columns = df.columns.to_series().apply(lambda x: x.strip())
            df.rename(
                columns={'Time Of Report (Year)': 'Year', 'Acute (Inc)': 'Cases', 'Sub-Clinical (Inc)': 'Subclinical'},
                inplace=True)

            # handle float year, say, 1969.997 to 1969
            df['Year'] = df['Year'].astype('int')

            # Verify total population by each region
            total_population_A = df[['HINT Group', 'Population']].groupby('HINT Group').sum().loc['Region:A'].values[0]
            total_population_B = df[['HINT Group', 'Population']].groupby('HINT Group').sum().loc['Region:B'].values[0]
            total_population_C = df[['HINT Group', 'Population']].groupby('HINT Group').sum().loc['Region:C'].values[0]
            total_population_D = df[['HINT Group', 'Population']].groupby('HINT Group').sum().loc['Region:D'].values[0]
            total_population = total_population_A + total_population_B + total_population_C + total_population_D
            # Verify each group (A,B,C,D) has rough 1/4 of population since we build demographic from HINT with:
            # Values = ["A", "B", "C", "D"],
            # InitialDistribution = [0.25, 0.25, 0.25, 0.25]
            delta = 0.05
            self.assertAlmostEqual(total_population_A / total_population, 0.25, delta=delta)
            self.assertAlmostEqual(total_population_B / total_population, 0.25, delta=delta)
            self.assertAlmostEqual(total_population_C / total_population, 0.25, delta=delta)
            self.assertAlmostEqual(total_population_D / total_population, 0.25, delta=delta)

            # Verify Newly_Infected by each region
            new_infection_by_year_A = df.loc[(df['HINT Group'] == 'Region:A')][['Year', "Newly Infected"]].groupby(
                'Year').sum()
            new_infection_by_year_B = df.loc[(df['HINT Group'] == 'Region:B')][['Year', "Newly Infected"]].groupby(
                'Year').sum()
            new_infection_by_year_C = df.loc[(df['HINT Group'] == 'Region:C')][['Year', "Newly Infected"]].groupby(
                'Year').sum()
            new_infection_by_year_D = df.loc[(df['HINT Group'] == 'Region:D')][['Year', "Newly Infected"]].groupby(
                'Year').sum()
            # Transmission from in AddIndividualPropertyAndHINT [0.0, 1.0, 2.0, 5.0]
            # For A->A is 0.
            # Verify first year, Region:A has some initial transmission which from outbreak
            self.assertTrue(new_infection_by_year_A.iloc[0].values[0] > 0)
            # Verify rest of years (no first year), Region:A Infected should be all 0
            self.assertTrue(all(n == 0 for n in new_infection_by_year_A.iloc[1:].squeeze().values))

            # Verify Infected by each region
            total_infected_A = df[['HINT Group', 'Infected']].groupby('HINT Group').sum().loc['Region:A'].values[0]
            total_infected_B = df[['HINT Group', 'Infected']].groupby('HINT Group').sum().loc['Region:B'].values[0]
            total_infected_C = df[['HINT Group', 'Infected']].groupby('HINT Group').sum().loc['Region:C'].values[0]
            total_infected_D = df[['HINT Group', 'Infected']].groupby('HINT Group').sum().loc['Region:D'].values[0]
            # verify for Region:B, total "Newly Infected" less than Region:C which less than Region:D
            # since for transmission rate A->B, rate is 1, A->C is 2, A->D is 5
            self.assertTrue(new_infection_by_year_B.sum().values[0] < new_infection_by_year_C.sum().values[0])
            self.assertTrue(new_infection_by_year_C.sum().values[0] < new_infection_by_year_D.sum().values[0])
            # verify total "Infected" B < C < D
            # also with proportion roughly 1:2:5
            self.assertTrue(total_infected_A > 0)
            self.assertTrue(total_infected_B < total_infected_C)
            self.assertTrue(total_infected_C < total_infected_D)

            # Verify Contagion Contact by regions
            # Verify Contact channel A should have zero values
            self.assertTrue(all(n==0 for n in property_list['Channels']['Contagion: Contact/Region:A']['Data']))
            # Verify all other contact channels should have non zero values
            self.assertTrue(sum(property_list['Channels']['Contagion: Contact/Region:B']['Data']) > 0)
            self.assertTrue(sum(property_list['Channels']['Contagion: Contact/Region:C']['Data']) > 0)
            self.assertTrue(sum(property_list['Channels']['Contagion: Contact/Region:D']['Data']) > 0)

            # verify contagion Environment by regions
            # Verify Environment channel A should have zero values
            self.assertTrue(all(n==0 for n in property_list['Channels']['Contagion: Environment/Region:A']['Data']))
            # Verify all other Environment channels should have non zero values
            self.assertTrue(sum(property_list['Channels']['Contagion: Environment/Region:B']['Data']) > 0)
            self.assertTrue(sum(property_list['Channels']['Contagion: Environment/Region:C']['Data']) > 0)
            self.assertTrue(sum(property_list['Channels']['Contagion: Environment/Region:D']['Data']) > 0)

    # This test to test transmission within groups
    def test_multiple_route_hint_no_mix(self):
        def build_demog1():
            import emodpy_typhoid.demographics.TyphoidDemographics as Demographics  # OK to call into emod-api

            demog = Demographics.from_template_node(lat=0, lon=0, pop=10000, name=1, forced_id=1)

            demog.AddIndividualPropertyAndHINT(Property="Region",
                                               Values=["A", "B", "C", "D"],
                                               InitialDistribution=[0.1, 0.2, 0.3, 0.4],
                                               TransmissionMatrix=[
                                                   [1.0, 0.0, 0.0, 0.0],
                                                   [0.0, 1.0, 0.0, 0.0],
                                                   [0.0, 0.0, 1.0, 0.0],
                                                   [0.0, 0.0, 0.0, 1.0]
                                               ],
                                               EnviroTransmissionMatrix=[
                                                   [1.0, 0.0, 0.0, 0.0],
                                                   [0.0, 1.0, 0.0, 0.0],
                                                   [0.0, 0.0, 1.0, 0.0],
                                                   [0.0, 0.0, 0.0, 1.0]
                                               ]
                                               )
            demog.generate_file(self._testMethodName + ".json")
            return demog

        task = EMODTask.from_default2(
            eradication_path=manifest.eradication_path,
            campaign_builder=build_camp,
            demog_builder=build_demog1,
            schema_path=manifest.schema_file,
            param_custom_cb=set_param_fn,
            ep4_custom_cb=None)

        print("Adding asset dir...")
        task.common_assets.add_directory(assets_directory=manifest.assets_input_dir)
        task.common_assets.add_asset(self._testMethodName + ".json")
        task.config.parameters.Demographics_Filenames = [self._testMethodName + ".json",
                                                         "TestDemographics_pak_updated.json"]
        task.config.parameters.Death_Rate_Dependence = "NONDISEASE_MORTALITY_BY_YEAR_AND_AGE_FOR_EACH_GENDER"
        task.config.parameters.Birth_Rate_Dependence = "INDIVIDUAL_PREGNANCIES_BY_AGE_AND_YEAR"
        task.config.parameters["Listed_Events"] = ["VaccineDistributed"]

        task.set_sif(manifest.sif)

        # Create simulation sweep with builder
        builder = SimulationBuilder()
        builder.add_sweep_definition(update_sim_random_seed, range(3))
        builder.add_sweep_definition(self.update_campaign_ip, ['Region:A'])
        # create experiment from builder
        experiment = Experiment.from_builder(builder, task, name=self.case_name)
        # The last step is to call run() on the ExperimentManager to run the simulations.
        experiment.run(wait_until_done=True, platform=self.platform)
        #exp_id = 'c40f487a-f267-ee11-92fc-f0921c167864'
        #experiment = self.platform.get_item(exp_id, item_type=ItemType.EXPERIMENT)
        task.handle_experiment_completion(experiment)
        task.get_file_from_comps(experiment.uid, ["PropertyReportTyphoid.json", "ReportTyphoidByAgeAndGender.csv"])
        # Get downloaded local ReportEventRecorder.csv file path for all simulations
        reporteventrecorder_downloaded = list(
            glob(os.path.join(experiment.id, "**/ReportTyphoidByAgeAndGender.csv"), recursive=True))
        propertyreport_downloaded = list(
            glob(os.path.join(experiment.id, "**/PropertyReportTyphoid.json"), recursive=True))
        reporteventrecorder_downloaded.sort()
        propertyreport_downloaded.sort()
        for i in range(len(reporteventrecorder_downloaded)):
            # read ReportEventRecorder.csv from each sim
            df = pd.read_csv(reporteventrecorder_downloaded[i])
            df.columns = df.columns.to_series().apply(lambda x: x.strip())
            with open(propertyreport_downloaded[i], "r") as content:
                property_list = json.loads(content.read())
            df.rename(
                columns={'Time Of Report (Year)': 'Year', 'Acute (Inc)': 'Cases', 'Sub-Clinical (Inc)': 'Subclinical'},
                inplace=True)

            # handle float year, say, 1969.997 to 1969
            df['Year'] = df['Year'].astype('int')

            # Verify total population by each region
            total_population_A = df[['HINT Group', 'Population']].groupby('HINT Group').sum().loc['Region:A'].values[0]
            total_population_B = df[['HINT Group', 'Population']].groupby('HINT Group').sum().loc['Region:B'].values[0]
            total_population_C = df[['HINT Group', 'Population']].groupby('HINT Group').sum().loc['Region:C'].values[0]
            total_population_D = df[['HINT Group', 'Population']].groupby('HINT Group').sum().loc['Region:D'].values[0]
            total_population = total_population_A + total_population_B + total_population_C + total_population_D
            # Values = ["A", "B", "C", "D"],
            # InitialDistribution = [0.1, 0.2, 0.3, 0.4]
            self.assertAlmostEqual(total_population_A / total_population, 0.1, delta=0.05)
            self.assertAlmostEqual(total_population_B / total_population, 0.2, delta=0.05)
            self.assertAlmostEqual(total_population_C / total_population, 0.3, delta=0.05)
            self.assertAlmostEqual(total_population_D / total_population, 0.4, delta=0.05)

            # Verify Newly_Infected by each region
            new_infection_by_year_A = df.loc[(df['HINT Group'] == 'Region:A')][['Year', "Newly Infected"]].groupby(
                'Year').sum()
            new_infection_by_year_B = df.loc[(df['HINT Group'] == 'Region:B')][['Year', "Newly Infected"]].groupby(
                'Year').sum()
            new_infection_by_year_C = df.loc[(df['HINT Group'] == 'Region:C')][['Year', "Newly Infected"]].groupby(
                'Year').sum()
            new_infection_by_year_D = df.loc[(df['HINT Group'] == 'Region:D')][['Year', "Newly Infected"]].groupby(
                'Year').sum()
            # Transmission from in AddIndividualPropertyAndHINT [1, 0, 0, 0]
            # For A->A has transmission from outbreak
            self.assertTrue(new_infection_by_year_A.squeeze().sum() > 0)
            # Verify rest of regions there is no transmission
            self.assertTrue(all(n == 0 for n in new_infection_by_year_B.squeeze().values))
            self.assertTrue(all(n == 0 for n in new_infection_by_year_C.squeeze().values))
            self.assertTrue(all(n == 0 for n in new_infection_by_year_D.squeeze().values))

            # Verify Infected by each region
            total_infected_sum = df[['HINT Group', 'Infected']].groupby('HINT Group').sum().reset_index()
            self.assertTrue(total_infected_sum['Infected'].values[0] > 0)  # Region:A
            self.assertTrue(all(n == 0 for n in total_infected_sum['Infected'].values[1:]))  # B, C, D

            # Verify Contagion Contact by regions
            # Verify Contact channel A should have non zero values
            self.assertTrue(sum(property_list['Channels']['Contagion: Contact/Region:A']['Data']) > 0)
            self.assertTrue(all(n == 0 for n in property_list['Channels']['Contagion: Contact/Region:B']['Data']))
            # Verify all other contact channels should have non values
            self.assertTrue(all(n == 0 for n in property_list['Channels']['Contagion: Contact/Region:B']['Data']))
            self.assertTrue(all(n == 0 for n in property_list['Channels']['Contagion: Contact/Region:C']['Data']))
            self.assertTrue(all(n == 0 for n in property_list['Channels']['Contagion: Contact/Region:D']['Data']))

            # verify contagion Environment by regions
            # Verify Environment channel A should have non zero values
            self.assertTrue(sum(property_list['Channels']['Contagion: Environment/Region:A']['Data']) > 0)
            # Verify all other Environment channels should have zero values
            self.assertTrue(all(n == 0 for n in property_list['Channels']['Contagion: Environment/Region:B']['Data']))
            self.assertTrue(all(n == 0 for n in property_list['Channels']['Contagion: Environment/Region:C']['Data']))
            self.assertTrue(all(n == 0 for n in property_list['Channels']['Contagion: Environment/Region:D']['Data']))

    def test_no_hint(self):
        def build_demog2():
            import emodpy_typhoid.demographics.TyphoidDemographics as Demographics  # OK to call into emod-api

            demog = Demographics.from_template_node(lat=0, lon=0, pop=10000, name=1, forced_id=1)

            demog.AddIndividualPropertyAndHINT(Property="Region",
                                               Values=["A", "B", "C", "D"],
                                               InitialDistribution=[0.1, 0.2, 0.3, 0.4],
                                               TransmissionMatrix=[
                                                   [1.0, 1.0, 1.0, 1.0],
                                                   [1.0, 1.0, 1.0, 1.0],
                                                   [1.0, 1.0, 1.0, 1.0],
                                                   [1.0, 1.0, 1.0, 1.0]
                                               ],
                                               EnviroTransmissionMatrix=[
                                                   [1.0, 1.0, 1.0, 1.0],
                                                   [1.0, 1.0, 1.0, 1.0],
                                                   [1.0, 1.0, 1.0, 1.0],
                                                   [1.0, 1.0, 1.0, 1.0]
                                               ]
                                               )
            demog.generate_file(self._testMethodName + ".json")
            return demog

        task = EMODTask.from_default2(
            eradication_path=manifest.eradication_path,
            campaign_builder=build_camp,
            demog_builder=build_demog2,
            schema_path=manifest.schema_file,
            param_custom_cb=set_param_fn,
            ep4_custom_cb=None)

        print("Adding asset dir...")
        task.common_assets.add_directory(assets_directory=manifest.assets_input_dir)
        task.common_assets.add_asset(self._testMethodName + ".json")
        task.config.parameters.Demographics_Filenames = [self._testMethodName + ".json", "TestDemographics_pak_updated.json"]
        task.config.parameters.Death_Rate_Dependence = "NONDISEASE_MORTALITY_BY_YEAR_AND_AGE_FOR_EACH_GENDER"
        task.config.parameters.Birth_Rate_Dependence = "INDIVIDUAL_PREGNANCIES_BY_AGE_AND_YEAR"
        task.config.parameters["Listed_Events"] = ["VaccineDistributed"]

        task.set_sif(manifest.sif)

        # Create simulation sweep with builder
        builder = SimulationBuilder()
        builder.add_sweep_definition(update_sim_random_seed, range(3))
        builder.add_sweep_definition(self.update_campaign_ip, ['Region:A'])
        # create experiment from builder
        experiment = Experiment.from_builder(builder, task, name=self.case_name)
        # The last step is to call run() on the ExperimentManager to run the simulations.
        experiment.run(wait_until_done=True, platform=self.platform)
        #exp_id = '0fa373e5-ee67-ee11-92fc-f0921c167864'
        #experiment = self.platform.get_item(exp_id, item_type=ItemType.EXPERIMENT)
        task.handle_experiment_completion(experiment)
        task.get_file_from_comps(experiment.uid, ["PropertyReportTyphoid.json", "ReportTyphoidByAgeAndGender.csv"])
        # Get downloaded local ReportEventRecorder.csv file path for all simulations
        reporteventrecorder_downloaded = list(
            glob(os.path.join(experiment.id, "**/ReportTyphoidByAgeAndGender.csv"), recursive=True))
        reporteventrecorder_downloaded.sort()
        for i in range(len(reporteventrecorder_downloaded)):
            # read ReportEventRecorder.csv from each sim
            df = pd.read_csv(reporteventrecorder_downloaded[i])
            df.columns = df.columns.to_series().apply(lambda x: x.strip())
            df.rename(
                columns={'Time Of Report (Year)': 'Year', 'Acute (Inc)': 'Cases', 'Sub-Clinical (Inc)': 'Subclinical'},
                inplace=True)

            # handle float year, say, 1969.997 to 1969
            df['Year'] = df['Year'].astype('int')
            # Verify total population by each region
            total_population_A = df[['HINT Group', 'Population']].groupby('HINT Group').sum().loc['Region:A'].values[0]
            total_population_B = df[['HINT Group', 'Population']].groupby('HINT Group').sum().loc['Region:B'].values[0]
            total_population_C = df[['HINT Group', 'Population']].groupby('HINT Group').sum().loc['Region:C'].values[0]
            total_population_D = df[['HINT Group', 'Population']].groupby('HINT Group').sum().loc['Region:D'].values[0]
            total_population = total_population_A + total_population_B + total_population_C + total_population_D
            # Values = ["A", "B", "C", "D"],
            # InitialDistribution = [0.1, 0.2, 0.3, 0.4]
            self.assertAlmostEqual(total_population_A / total_population, 0.1, delta=0.05)
            self.assertAlmostEqual(total_population_B / total_population, 0.2, delta=0.05)
            self.assertAlmostEqual(total_population_C / total_population, 0.3, delta=0.05)
            self.assertAlmostEqual(total_population_D / total_population, 0.4, delta=0.05)

            new_infection_by_year_A = df.loc[(df['HINT Group'] == 'Region:A')][['Year', "Newly Infected"]].groupby(
                'Year').sum()
            new_infection_by_year_B = df.loc[(df['HINT Group'] == 'Region:B')][['Year', "Newly Infected"]].groupby(
                'Year').sum()
            new_infection_by_year_C = df.loc[(df['HINT Group'] == 'Region:C')][['Year', "Newly Infected"]].groupby(
                'Year').sum()
            new_infection_by_year_D = df.loc[(df['HINT Group'] == 'Region:D')][['Year', "Newly Infected"]].groupby(
                'Year').sum()
            # verify if the first row and first column for each region has the biggest value bc transmission can go
            # everywhere and start from first timestamp
            self.assertTrue(new_infection_by_year_A.iloc[0, 0] == new_infection_by_year_A.max().max())
            self.assertTrue(new_infection_by_year_B.iloc[0, 0] == new_infection_by_year_B.max().max())
            self.assertTrue(new_infection_by_year_C.iloc[0, 0] == new_infection_by_year_C.max().max())
            self.assertTrue(new_infection_by_year_D.iloc[0, 0] == new_infection_by_year_D.max().max())
            # verify A < B < C < D for "Newly Infected" value since population is A < B < C < D
            self.assertTrue(new_infection_by_year_A.sum().values[0] < new_infection_by_year_B.sum().values[0])
            self.assertTrue(new_infection_by_year_B.sum().values[0] < new_infection_by_year_C.sum().values[0])
            self.assertTrue(new_infection_by_year_C.sum().values[0] < new_infection_by_year_D.sum().values[0])

            total_infected_sum = df[['HINT Group', 'Infected']].groupby('HINT Group').sum().reset_index()

            self.assertTrue(
                total_infected_sum['Infected'].values[0] < total_infected_sum['Infected'].values[1])  # A < B
            self.assertTrue(
                total_infected_sum['Infected'].values[1] < total_infected_sum['Infected'].values[2])  # B < C
            self.assertTrue(
                total_infected_sum['Infected'].values[2] < total_infected_sum['Infected'].values[3])  # C < D

    def test_multiple_route_hint_env(self):
        def build_demog3():
            import emodpy_typhoid.demographics.TyphoidDemographics as Demographics  # OK to call into emod-api

            demog = Demographics.from_template_node(lat=0, lon=0, pop=10000, name=1, forced_id=1)

            demog.AddIndividualPropertyAndHINT(Property="Region",
                                               Values=["A", "B", "C", "D"],
                                               InitialDistribution=[0.1, 0.2, 0.3, 0.4],
                                               TransmissionMatrix=[
                                                   [1.0, 0.0, 0.0, 0.0],
                                                   [0.0, 1.0, 0.0, 0.0],
                                                   [0.0, 0.0, 1.0, 0.0],
                                                   [0.0, 0.0, 0.0, 1.0]
                                               ],
                                               EnviroTransmissionMatrix=[
                                                   [0.0, 2.0, 0.0, 0.0],
                                                   [0.0, 0.0, 2.0, 0.0],
                                                   [0.0, 0.0, 0.0, 2.0],
                                                   [0.0, 0.0, 0.0, 0.0]
                                               ]
                                               )
            demog.generate_file(self._testMethodName + ".json")
            return demog

        task = EMODTask.from_default2(
            eradication_path=manifest.eradication_path,
            campaign_builder=build_camp,
            demog_builder=build_demog3,
            schema_path=manifest.schema_file,
            param_custom_cb=set_param_fn,
            ep4_custom_cb=None)

        print("Adding asset dir...")
        task.common_assets.add_directory(assets_directory=manifest.assets_input_dir)
        task.common_assets.add_asset(self._testMethodName + ".json")
        task.config.parameters.Demographics_Filenames = [self._testMethodName + ".json", "TestDemographics_pak_updated.json"]
        task.config.parameters.Death_Rate_Dependence = "NONDISEASE_MORTALITY_BY_YEAR_AND_AGE_FOR_EACH_GENDER"
        task.config.parameters.Birth_Rate_Dependence = "INDIVIDUAL_PREGNANCIES_BY_AGE_AND_YEAR"
        task.config.parameters["Listed_Events"] = ["VaccineDistributed"]

        task.set_sif(manifest.sif)

        # Create simulation sweep with builder
        builder = SimulationBuilder()
        builder.add_sweep_definition(update_sim_random_seed, range(3))
        builder.add_sweep_definition(self.update_campaign_ip, ['Region:A'])
        # create experiment from builder
        experiment = Experiment.from_builder(builder, task, name=self.case_name)
        # The last step is to call run() on the ExperimentManager to run the simulations.
        experiment.run(wait_until_done=True, platform=self.platform)
        #exp_id = 'f0e29cf9-fd67-ee11-92fc-f0921c167864'
        #experiment = self.platform.get_item(exp_id, item_type=ItemType.EXPERIMENT)
        task.handle_experiment_completion(experiment)
        task.get_file_from_comps(experiment.uid, ["PropertyReportTyphoid.json", "ReportTyphoidByAgeAndGender.csv"])
        # Get downloaded local ReportEventRecorder.csv file path for all simulations
        reporteventrecorder_downloaded = list(
            glob(os.path.join(experiment.id, "**/ReportTyphoidByAgeAndGender.csv"), recursive=True))
        propertyreport_downloaded = list(
            glob(os.path.join(experiment.id, "**/PropertyReportTyphoid.json"), recursive=True))
        reporteventrecorder_downloaded.sort()
        propertyreport_downloaded.sort()
        for i in range(len(reporteventrecorder_downloaded)):
            # read ReportEventRecorder.csv from each sim
            df = pd.read_csv(reporteventrecorder_downloaded[i])
            df.columns = df.columns.to_series().apply(lambda x: x.strip())
            with open(propertyreport_downloaded[i], "r") as content:
                property_list = json.loads(content.read())
            df.rename(
                columns={'Time Of Report (Year)': 'Year', 'Acute (Inc)': 'Cases', 'Sub-Clinical (Inc)': 'Subclinical'},
                inplace=True)

            # handle float year, say, 1969.997 to 1969
            df['Year'] = df['Year'].astype('int')

            # Verify total population by each region
            total_population_A = df[['HINT Group', 'Population']].groupby('HINT Group').sum().loc['Region:A'].values[0]
            total_population_B = df[['HINT Group', 'Population']].groupby('HINT Group').sum().loc['Region:B'].values[0]
            total_population_C = df[['HINT Group', 'Population']].groupby('HINT Group').sum().loc['Region:C'].values[0]
            total_population_D = df[['HINT Group', 'Population']].groupby('HINT Group').sum().loc['Region:D'].values[0]
            total_population = total_population_A + total_population_B + total_population_C + total_population_D
            # Values = ["A", "B", "C", "D"],
            # InitialDistribution = [0.1, 0.2, 0.3, 0.4]
            self.assertAlmostEqual(total_population_A / total_population, 0.1, delta=0.05)
            self.assertAlmostEqual(total_population_B / total_population, 0.2, delta=0.05)
            self.assertAlmostEqual(total_population_C / total_population, 0.3, delta=0.05)
            self.assertAlmostEqual(total_population_D / total_population, 0.4, delta=0.05)

            # verify contact/environment channel start time in order. i.e A>B>C>D
            geographic_zones = ["A", "B", "C", "D"]
            contact_chans = {}
            enviro_chans = {}
            success = True
            for zone in geographic_zones:
                contact_chans[zone] = property_list["Channels"]["Contagion: Contact/Region:" + zone]["Data"]
                enviro_chans[zone] = property_list["Channels"]["Contagion: Environment/Region:" + zone]["Data"]
            last_cont_contagion_appearance_tstep = 0
            last_env_contagion_appearance_tstep = 0
            for zone in geographic_zones:
                if max(contact_chans[zone]) == 0:
                    print("We didn't find any contagion in this zone. Bad.")
                    success = False
                first_contagion_timestep = find_first(contact_chans[zone])
                if first_contagion_timestep < last_cont_contagion_appearance_tstep:
                    print("Contagion (contact) appeared in zone too early. Bad.")
                    success = False
                last_cont_contagion_appearance_tstep = first_contagion_timestep

            for zone in geographic_zones[1:]:
                if max(enviro_chans[zone]) == 0:
                    print("We didn't find any contagion in this zone. Bad.")
                    success = False
                first_contagion_timestep = find_first(enviro_chans[zone])
                if first_contagion_timestep < last_env_contagion_appearance_tstep:
                    print("Contagion (enviro) appeared in zone too early. Bad.")
                    success = False
                last_env_contagion_appearance_tstep = first_contagion_timestep
            self.assertTrue(success == True)


if __name__ == '__main__':
    unittest.main()
