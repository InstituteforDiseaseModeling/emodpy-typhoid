import os
import sys
from functools import partial

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append('../')
from hint_test_helper import TestAgeBaseHint, build_camp, build_demog_target_one_age_bin, set_param_fn


class TestAgeBaseHintTargetOneAgeBin(TestAgeBaseHint):
    """
    A test class that submit SFTs to Comps and run the dtk_post_process.py in ep4_dir folder and write the SFT result
    as a tag of for the simulation in Comps.
    Each test case will define a build_demog function and call the main test function in the base class as
    self.age_base_hint_test(build_demog).
    """
    @classmethod
    def setUpClass(cls):
        cls.test_name = os.path.basename(__file__)

    def test_age_base_hint_targe_first_age_bin(self):
        build_demog = partial(build_demog_target_one_age_bin, group_index=0, value=1)
        self.age_base_hint_test(build_demog)

    def test_age_base_hint_targe_second_age_bin(self):
        build_demog = partial(build_demog_target_one_age_bin, group_index=1, value=0.5)
        self.age_base_hint_test(build_demog)

    def test_age_base_hint_targe_third_age_bin(self):
        build_demog = partial(build_demog_target_one_age_bin, group_index=2, value=0.8)
        self.age_base_hint_test(build_demog)

    def test_age_base_hint_targe_last_age_bin(self):
        build_demog = partial(build_demog_target_one_age_bin, group_index=3, value=2)
        self.age_base_hint_test(build_demog)


if __name__ == '__main__':
    import unittest
    unittest.main()
