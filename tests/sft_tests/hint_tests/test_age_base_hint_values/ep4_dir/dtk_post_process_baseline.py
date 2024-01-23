#!/usr/bin/python
import os.path
import json
import pandas as pd
import matplotlib.pyplot as plt

from idm_test.dtk_test.sft_class import arg_parser, SFT


class AgeBaseHINTValueTest(SFT):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    # overwrite the test method
    def test(self):
        self.success = True

        # Load Age Base HINT parameters from Demographics file
        age_bin_edges_in_years = [0, 5, 20, 60, -1]

        # Replace the last age bin edge -1 with a large year of age. It will be used to generate the IntervalIndex for
        # dataframe later.
        age_bin_edges_in_years[-1] = 125

        with open(self.report_name, "w") as outfile:
            outfile.write("This simulation generate a baseline to be compared with other simulations.")
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
