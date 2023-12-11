import os
import sys
from functools import partial

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append('../')
from hint_test_helper import TestAgeBaseHint, build_camp, build_demog, set_param_fn, Age_Bin_Edges_In_Years, \
    num_age_bin, build_demog_target_all_age_bin


def build_demog_age_bins():
    """
    Build a demographics input file for the DTK using emod_api with AgeDependentTransmission matrix. The transmission
    matrix will have a constant value for one group and 0 for the other groups
    """
    demog = build_demog()
    TransmissionMatrix = [[0] * num_age_bin for _ in range(num_age_bin)]

    group_indexes = [0, 1, 2, 3]
    values = [2, 1, 0.5, 0.1]

    for row in TransmissionMatrix:
        for group_index in group_indexes:
            row[group_index] = values[group_index]

    demog.AddAgeDependentTransmission(
        Age_Bin_Edges_In_Years=Age_Bin_Edges_In_Years.copy(),
        TransmissionMatrix=TransmissionMatrix
    )

    return demog


class TestAgeBaseHintValues(TestAgeBaseHint):
    @classmethod
    def setUpClass(cls):
        cls.test_name = os.path.basename(__file__)

    def test_age_base_hint_values(self):
        self.age_base_hint_test(build_demog_age_bins)

    def test_age_base_hint_values_baseline(self):
        # This is a baseline simulation that is run without the AgeBadeHINT feature.
        self.age_base_hint_test(build_demog)

    def test_age_base_hint_values_all_0s(self):
        build_demog_age_bins_all_0s = partial(build_demog_target_all_age_bin, value=0)
        self.age_base_hint_test(build_demog_age_bins_all_0s)

    def test_age_base_hint_values_all_1s(self):
        build_demog_age_bins_all_1s = partial(build_demog_target_all_age_bin, value=1)
        self.age_base_hint_test(build_demog_age_bins_all_1s)

    def test_age_base_hint_values_all_2s(self):
        build_demog_age_bins_all_2s = partial(build_demog_target_all_age_bin, value=2)
        self.age_base_hint_test(build_demog_age_bins_all_2s)

    def test_age_base_hint_values_all_halves(self):
        build_demog_age_bins_all_halves = partial(build_demog_target_all_age_bin, value=0.5)
        self.age_base_hint_test(build_demog_age_bins_all_halves)


if __name__ == '__main__':
    import unittest
    unittest.main()
