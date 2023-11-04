#!/usr/bin/python
import math
import os.path

import pandas as pd

from idm_test.dtk_test.sft_class import arg_parser, SFT

class HINTCrossTest(SFT):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    # overwrite the test method
    def test(self):
        self.success = False
        with open(self.report_name, "w") as outfile:
            with open(os.path.join(self.output_folder, "ReportTyphoidByAgeAndGender.csv"), 'r') as infile:
                df = pd.read_csv(infile)
                df.columns = df.columns.to_series().apply(lambda x: x.strip())
                new_infected_urban = df.loc[(df['HINT Group'] == 'Region:Urban')][['Newly Infected']]
                new_infected_rural = df.loc[(df['HINT Group'] == 'Region:Rural')][['Newly Infected']]
                # verify both region should have some new infections. Region:Urban infections are from original outbreak
                # Region:Rural's new infections are from Region:Urban
                if new_infected_urban['Newly Infected'].notna().any() and new_infected_rural['Newly Infected'].notna().any():
                    self.success = True
                    outfile.write("GOOD: There is some transmission for IP Region:Urban and Region:Rural \n")
                    outfile.write("Part1: Result is True.\n")
                else:
                    self.success = False
                    outfile.write("BAD: There should have some transmission for both regoins\n")
                    outfile.write("Part1: Result is False.\n")
                population_buran = df.loc[(df['HINT Group'] == 'Region:Urban')][['Population']].sum().values[0]
                population_rural = df.loc[(df['HINT Group'] == 'Region:Rural')][['Population']].sum().values[0]
                ratio = population_rural/population_buran
                expected_ration = 0.8/0.2
                if not math.isclose(ratio, expected_ration, abs_tol=0.5):
                    self.success = False
                    outfile.write(f"    BAD: population ration is not correct")
                    outfile.write("Part2: Population test  is failed.\n")
                else:
                    self.success = True
                    outfile.write(f"    GOOD: population ration is correct\n")
                    outfile.write("Part2: Population test  is passed.\n")
        return self.success


def application(output_folder="output", my_arg=None):
    if not my_arg:
        my_sft = HINTCrossTest(stdout='stdout.txt')
    else:
        my_sft = HINTCrossTest(
            output=my_arg.output, stdout='stdout.txt', json_report=my_arg.json_report, event_csv=my_arg.event_csv,
            config=my_arg.config, campaign=my_arg.campaign, report_name=my_arg.report_name, debug=my_arg.debug)
    my_sft.run()


if __name__ == "__main__":
    # execute only if run as a script
    my_arg = arg_parser()
    application(my_arg=my_arg)
