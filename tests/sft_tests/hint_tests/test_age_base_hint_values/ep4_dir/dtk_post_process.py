#!/usr/bin/python
import os.path
import json
import pandas as pd
import matplotlib.pyplot as plt

from idm_test.dtk_test.sft_class import arg_parser, SFT


class AgeBaseHINTValueTest(SFT):
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
        age_bin_edges_in_years[-1] = 125

        with open(self.report_name, "w") as outfile:
            if contact != environmental:
                self.success = False
                outfile.write(
                    f"BAD: Expected the same transmission matix for both contact and environmental routes. Found:"
                    f" contact = {contact}, environmental = {environmental}.\n")
            else:
                transmission_matrix = contact
                for transmission_rate in transmission_matrix:
                    for idx, x in enumerate(transmission_matrix[0]):
                        if transmission_rate[idx] != x:
                            self.success = False
                            outfile.write(
                                f"BAD: Expected the same transmission rate for the same age bin. please check the "
                                f"TransmissionMatrix.\n")
                            break
                if self.success:
                    with open(os.path.join(self.output_folder, "ReportEventRecorder.csv"), 'r') as infile:
                        df = pd.read_csv(infile)
                        df.columns = df.columns.to_series().apply(lambda x: x.strip())
                        # Filter the dataframe for NewInfectionEvent
                        new_infected_df = df.loc[(df['Event_Name'] == 'NewInfectionEvent')]
                        # Add a new 'Age_Year' column to the DataFrame by converting 'Age' to years.
                        new_infected_df['Age_Year'] = new_infected_df['Age'] / 365.0
                        # Add a new 'Age_Bin' column to the DataFrame based on age bin edges.
                        bins = pd.IntervalIndex.from_breaks(age_bin_edges_in_years)
                        new_infected_df['Age_Bin'] = pd.cut(new_infected_df['Age_Year'], bins=bins, right=False).astype(str)

                        # Save dataframes to csv for debugging
                        new_infected_df.to_csv("ReportEventRecorder_AgeBin.csv")

                        # ignore the first timestep where we have the outbreak
                        new_infected_df = new_infected_df.loc[(new_infected_df['Year'] != 2005)]

                        # Count NewInfectionEvent by Age_Bin
                        count_dict = {age_bin: count for age_bin, count in new_infected_df.groupby('Age_Bin').size().items()}

                        # Plot the dictionary into histogram plot for debugging
                        if len(count_dict):
                            self.plot_bar(count_dict)
                            outfile.write(f'{count_dict}\n')

                        for idx, rate in enumerate(transmission_matrix[0]):
                            left = age_bin_edges_in_years[idx]
                            right = age_bin_edges_in_years[idx + 1]
                            # age_bin_interval = str(pd.Interval(left=left, right=right, closed='right'))
                            # workaround for old Pandas library
                            age_bin_interval = f'({left:.1f}, {right:.1f}]'
                            if rate == 0:
                                if age_bin_interval in count_dict:
                                    self.success = False
                                    outfile.write(
                                        f"BAD: Expected no transmission in age bin {age_bin_interval} since "
                                        f"transmission rate is 0.\n")
                                else:
                                    outfile.write(
                                        f"GOOD: There is no transmission in age bin {age_bin_interval} since "
                                        f"transmission rate is 0.\n")
                            else:
                                if age_bin_interval in count_dict and count_dict[age_bin_interval] != 0:
                                    outfile.write(
                                        f"GOOD: There are {count_dict[age_bin_interval]} transmission in age bin "
                                        f"{age_bin_interval} since transmission rate is {rate}.\n")
                                else:
                                    self.success = False
                                    outfile.write(
                                        f"BAD: There is no transmission in age bin {age_bin_interval} but "
                                        f"transmission rate is {rate} != 0.\n")
        return self.success

    def plot_bar(self, count_dict):
        # Extract keys and values from the dictionary
        keys = list(count_dict.keys())
        values = list(count_dict.values())
        # Create a histogram
        plt.bar(keys, values)
        # Set labels for the axes
        plt.xlabel('Age bin')
        plt.ylabel('New Infections')
        # Set the title of the graph
        plt.title('Histogram of New Infection Values')
        plt.savefig('new_infection_count_by_age_bin.png')
        plt.close()


def application(output_folder="output", my_arg=None):
    if not my_arg:
        my_sft = AgeBaseHINTValueTest(stdout='stdout.txt')
    else:
        my_sft = AgeBaseHINTValueTest(
            output=my_arg.output, stdout='stdout.txt', json_report=my_arg.json_report, event_csv=my_arg.event_csv,
            config=my_arg.config, campaign=my_arg.campaign, report_name=my_arg.report_name, debug=my_arg.debug)
    my_sft.run()


if __name__ == "__main__":
    # execute only if run as a script
    my_arg = arg_parser()
    application(my_arg=my_arg)
