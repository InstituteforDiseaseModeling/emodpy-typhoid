#!/usr/bin/env python

from idmtools.core.platform_factory import Platform
from idmtools_platform_comps.utils.singularity_build import SingularityBuildWorkItem

if __name__ == '__main__':
    platform = Platform("CALCULON")
    sbi = SingularityBuildWorkItem(name="Create sif from Artifactory dockerfile", definition_file="dtk_run_centos_py36_r.def", image_name="my_shiny_new.sif")
    sbi.tags = dict(ubuntu="20.04") # not true
    sbi.run(wait_until_done=True, platform=platform)
    if sbi.succeeded:
        # Write ID file
        sbi.asset_collection.to_id_file("my_shiny_new.id")
