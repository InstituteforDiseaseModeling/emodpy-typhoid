#!/usr/bin/python

import json
import os.path

import numpy as np
import pandas as pd

from idm_test.dtk_test.general_support import InsetKeys, ConfigKeys, CampaignKeys, load_config_parameters
from idm_test.dtk_test.sft_class import arg_parser, SFT

with open("config.json") as infile:
    run_number = json.load(infile)['parameters']['Run_Number']
np.random.seed(run_number)
import math

from idm_test.dtk_test import sft

channels = [InsetKeys.ChannelsKeys.Infected,
            InsetKeys.ChannelsKeys.New_Infections,
            InsetKeys.ChannelsKeys.Statistical_Population]

config_keys = [ConfigKeys.Base_Individual_Sample_Rate,
               ConfigKeys.Simulation_Timestep,
               ConfigKeys.Simulation_Duration,
               "Base_Year"]


class Stdout:
    dose = "gave out "
    stat_pop = "StatPop: "


matches = ["'SimpleVaccine' interventions at ",
           "StatPop: "
           ]


def load_campaign_file(campaign_filename, debug):
    with open(campaign_filename) as infile:
        cf = json.load(infile)
    campaign_obj = {CampaignKeys.Start_Day: [], CampaignKeys.Demographic_Coverage: [],
                    CampaignKeys.Property_Restrictions: []}
    events = cf[CampaignKeys.Events]
    for event in events:
        start_day = event[CampaignKeys.Start_Day]
        campaign_obj[CampaignKeys.Start_Day].append(int(start_day))
        if event[CampaignKeys.Event_Coordinator_Config][CampaignKeys.Intervention_Config][
            CampaignKeys.class_key] != CampaignKeys.InterventionClassKeys.OutbreakIndividual:
            coverage = event[CampaignKeys.Event_Coordinator_Config][CampaignKeys.Intervention_Config][
                CampaignKeys.Demographic_Coverage]
            campaign_obj[CampaignKeys.Demographic_Coverage].append(float(coverage))
        else:
            coverage = event[CampaignKeys.Event_Coordinator_Config][CampaignKeys.Demographic_Coverage]
            campaign_obj[CampaignKeys.Demographic_Coverage].append(float(coverage))

    if debug:
        with open("DEBUG_campaign_object.json", 'w') as outfile:
            json.dump(campaign_obj, outfile, indent=4)

    return campaign_obj


def parse_stdout_file(stdout_filename="stdout.txt", simulation_timestep=1, debug=True):
    filtered_lines = []
    with open(stdout_filename) as logfile:
        for line in logfile:
            if sft.has_match(line, matches):
                filtered_lines.append(line)
    if debug:
        with open("DEBUG_filtered_lines.txt", "w") as outfile:
            outfile.writelines(filtered_lines)

    # initialize variables
    for line in filtered_lines:
        if matches[0] in line:
            dose = int(sft.get_val(Stdout.dose, line))
        elif matches[1] in line and str(simulation_timestep) in line:
            population_at_time = int(sft.get_val(Stdout.stat_pop, line))
    return dose, population_at_time


class VaxRolloutCoverageTest(SFT):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.params = load_config_parameters(self.config_filename, config_keys, self.debug)
        self.campaign_obj = load_campaign_file(self.campaign_filename, self.debug)
        from idm_test.dtk_test.output_file import ReportEventRecorder
        self.report_event_recorder_csv = ReportEventRecorder(
            file=os.path.join(self.output_folder, self.event_report_name))

    # overwrite the test method
    def test(self):
        self.success = False
        with open(self.report_name, "w") as outfile:
            campain_cax_start = int(self.campaign_obj['Start_Day'][2] / 365) + self.params['Base_Year']
            df = self.report_event_recorder_csv.df
            # Baby born in last 9 month before simulation ends may not get vaxed
            end_caculate_birth_time = ((self.params['Simulation_Duration'] / 365 + self.params['Base_Year']) * 365 - (
                        9 * 30 + 7)) / 365
            births_id = \
                df.loc[(df['Year'] >= campain_cax_start) & (df['Event_Name'] == 'Births') & (
                            df['Year'] < end_caculate_birth_time)][
                    ['Event_Name', 'Year', "Age", "Individual_ID"]].sort_values(by='Year', ascending=True)
            vax_id = df.loc[(df['Year'] >= campain_cax_start) & (df['Event_Name'] == 'VaccineDistributed2')][
                ['Event_Name', 'Year', "Age", "Individual_ID"]].sort_values(by='Year', ascending=True)
            total_vax_count = vax_id.shape[0]
            total_birth_count = births_id.shape[0]
            actual_vax_coverage = total_vax_count / total_birth_count
            expected_coverage = self.campaign_obj['Demographic_Coverage'][2]
            # set the base tolerance to 5% for coverage == 1,
            # there is an uniform delay period with 14 days time window that we need to consider.
            tolerance = 0.05
            if expected_coverage != 1:
                from idm_test.stats_test import cal_tolerance_binomial
                # add the tolerance calculated based on binomial probabality on top of the base tolerance(discounted based on coverage)
                tolerance = max(0, tolerance * (1 - (1 - expected_coverage) * 2))
                tolerance += cal_tolerance_binomial(expected_coverage * total_vax_count, expected_coverage, prob=0.05)

            if not math.isclose(actual_vax_coverage, expected_coverage, abs_tol=tolerance):
                self.success = False
                outfile.write(
                    f"    BAD: at time step {self.campaign_obj['Start_Day'][2]}, vax coverage {actual_vax_coverage},"
                    f" expected {expected_coverage} with tolerance = {tolerance}.\n")
                outfile.write("Result is False.\n")
            else:
                self.success = True
                outfile.write(f"    GOOD: at time step {self.campaign_obj['Start_Day'][2]}, vax coverage "
                              f"{actual_vax_coverage}, expected {expected_coverage} with tolerance = {tolerance}.\n"
                              "    GOOD: coverage is correct!\n")
                outfile.write("Result is True.\n")
        return self.success


def application(output_folder="output", my_arg=None):
    if not my_arg:
        my_sft = VaxRolloutCoverageTest(stdout='stdout.txt')
    else:
        my_sft = VaxRolloutCoverageTest(
            output=my_arg.output, stdout='stdout.txt', json_report=my_arg.json_report, event_csv=my_arg.event_csv,
            config=my_arg.config, campaign=my_arg.campaign, report_name=my_arg.report_name, debug=my_arg.debug)
    my_sft.run()


if __name__ == "__main__":
    # execute only if run as a script
    my_arg = arg_parser()
    application(my_arg=my_arg)
