#!/usr/bin/python
import os.path
import json
import pandas as pd

from idm_test.dtk_test.sft_class import arg_parser, SFT


class AgeBaseHINTTargetTest(SFT):
    """
    SFTs that testing the targeting Age Bin in the Age Bin HINT TransmissionMatrix.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_age_base_hint_matrix(self):
        """
        load the demographics json and get the age base HINT related data
        """
        with open('Assets/demographics.json', 'r') as f:
            demog = json.load(f)
            age_bin_edges_in_years = demog['Defaults']['IndividualProperties'][0]['Age_Bin_Edges_In_Years']
            transmission_matrix = demog['Defaults']['IndividualProperties'][0]['TransmissionMatrix']
            contact = transmission_matrix['contact']['Matrix']
            environmental = transmission_matrix['environmental']['Matrix']
            return age_bin_edges_in_years, contact, environmental

    # overwrite the test method
    def test(self):
        self.success = True

        # Load Age Base HINT parameters from Demographics file
        age_bin_edges_in_years, contact, environmental = self.get_age_base_hint_matrix()

        # Replace the last age bin edge -1 with a large year of age. It will be used to generate the IntervalIndex for
        # dataframe later.
        age_bin_edges_in_years[-1] = 150

        with open(self.report_name, "w") as outfile:
            if contact != environmental:
                self.success = False
                outfile.write(
                    f"BAD: Expected the same transmission matix for both contact and environmental routes. Found:"
                    f" contact = {contact}, environmental = {environmental}.\n")
            else:
                transmission_matrix = contact
                found_group = None
                for idx, x in enumerate(transmission_matrix[0]):
                    if x != 0:
                        found_group = idx
                        break
                if found_group is None:
                    self.success = False
                    outfile.write(
                        f"BAD: Expected some non zero value in TransmissionMatrix. Please check TransmissionMatrix = "
                        f"{transmission_matrix}\n")
                else:
                    with open(os.path.join(self.output_folder, "ReportEventRecorder.csv"), 'r') as infile:
                        df = pd.read_csv(infile)
                        df.columns = df.columns.to_series().apply(lambda x: x.strip())
                        # Filter the dataframe for NewInfectionEvent
                        new_infected_df = df.loc[(df['Event_Name'] == 'NewInfectionEvent')]
                        # Add a new 'Age_Year' column to the DataFrame by converting 'Age' to years.
                        new_infected_df['Age_Year'] = new_infected_df['Age'] / 365.0
                        # Add a new 'Age_Bin' column to the DataFrame based on age bin edges.
                        bins = pd.IntervalIndex.from_breaks(age_bin_edges_in_years)
                        new_infected_df['Age_Bin'] = pd.cut(new_infected_df['Age_Year'], bins=bins, right=False)

                        # Count NewInfectionEvent by timestamp and Age_Bin
                        count_df = new_infected_df.groupby(['Year', 'Age_Bin']).size().reset_index(name='Count')
                        count_df.reset_index(drop=True, inplace=True)

                        # Save dataframes to csv for debugging
                        new_infected_df.to_csv("ReportEventRecorder_AgeBin.csv")
                        count_df.to_csv("ReportEventRecorder_AgeBin_Count.csv")

                        # ignore the first timestep where we have the outbreak
                        labels = pd.unique(count_df['Age_Bin']).tolist()
                        count_df = count_df.loc[(count_df['Year'] != 2005)]
                        outfile.write(f"Age Bins: {labels}.\n")
                        left = age_bin_edges_in_years[found_group]
                        right = age_bin_edges_in_years[found_group+1]
                        expected_age_bin_interval = pd.Interval(left=left, right=right, closed='right')

                        for label in labels:
                            if label != expected_age_bin_interval:
                                if count_df.loc[count_df['Age_Bin'] == label]['Count'].sum() != 0:
                                    self.success = False
                                    outfile.write(f"BAD: Expected no transmission for age bin: {label}, found "
                                                  f"{count_df.loc[count_df['Age_Bin'] == label]['Count'].sum()} new infections.\n")
                                else:
                                    outfile.write(f"Good: There is no transmission for age bin: {label}.\n")
                            else:
                                new_infection_total = count_df.loc[count_df['Age_Bin'] == label]['Count'].sum()
                                if new_infection_total == 0:
                                    self.success = False
                                    outfile.write(f"BAD: Expected some transmissions for age bin: {label}, found 0 "
                                                  f"new infection.\n")
                                else:
                                    outfile.write(f"Good: There are some transmission for age bin: {label},found "
                                                  f"{new_infection_total} new infection.\n")

        return self.success


def application(output_folder="output", my_arg=None):
    if not my_arg:
        my_sft = AgeBaseHINTTargetTest(stdout='stdout.txt')
    else:
        my_sft = AgeBaseHINTTargetTest(
            output=my_arg.output, stdout='stdout.txt', json_report=my_arg.json_report, event_csv=my_arg.event_csv,
            config=my_arg.config, campaign=my_arg.campaign, report_name=my_arg.report_name, debug=my_arg.debug)
    my_sft.run()


if __name__ == "__main__":
    # execute only if run as a script
    my_arg = arg_parser()
    application(my_arg=my_arg)
