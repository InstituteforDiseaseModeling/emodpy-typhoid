#!/usr/bin/python

import os.path

import pandas as pd

from idm_test.dtk_test.sft_class import arg_parser, SFT

class HINTNoMixTest(SFT):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    # overwrite the test method
    def test(self):
        self.success = False
        with open(self.report_name, "w") as outfile:
            with open(os.path.join(self.output_folder, "ReportTyphoidByAgeAndGender.csv"), 'r') as infile:
                df = pd.read_csv(infile)
                df.columns = df.columns.to_series().apply(lambda x: x.strip())
                new_infected = df.loc[(df['HINT Group'] == 'Region:Urban')][['Newly Infected']]
                if (new_infected['Newly Infected'] == 0).all():
                    self.success = True
                    outfile.write("GOOD: There is no transmission for IP Region:Urban \n")
                    outfile.write("Part1: Result is True.\n")
                else:
                    self.success = False
                    outfile.write("BAD: There should be no transmission for IP Region:Urban\n")
                    outfile.write("Part1: Result is False.\n")
        return self.success


def application(output_folder="output", my_arg=None):
    if not my_arg:
        my_sft = HINTNoMixTest(stdout='stdout.txt')
    else:
        my_sft = HINTNoMixTest(
            output=my_arg.output, stdout='stdout.txt', json_report=my_arg.json_report, event_csv=my_arg.event_csv,
            config=my_arg.config, campaign=my_arg.campaign, report_name=my_arg.report_name, debug=my_arg.debug)
    my_sft.run()


if __name__ == "__main__":
    # execute only if run as a script
    my_arg = arg_parser()
    application(my_arg=my_arg)
