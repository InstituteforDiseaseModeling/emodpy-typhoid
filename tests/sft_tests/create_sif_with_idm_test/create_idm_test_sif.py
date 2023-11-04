from COMPS.utils.get_output_files_for_workitem import get_files
from idmtools.assets import AssetCollection, Asset

from idmtools.core.platform_factory import Platform
from idmtools_platform_comps.utils.singularity_build import SingularityBuildWorkItem

if __name__ == '__main__':
    platform = Platform("SlurmStage")
    sbi = SingularityBuildWorkItem(name="Create emodpy-typhoid-idm-test",  definition_file="my_shiny_new_idm_test.def", image_name="my_shiny_new_idm_test.sif", force=True)
    ac = AssetCollection()
    sbi.add_assets(AssetCollection.from_id_file("dtk_centos_2018_stage.id"))
    ac_obj = sbi.run(wait_until_done=True, platform=platform)

    if sbi.succeeded:
        print("sbi.id: ", sbi.id)
        # Write ID file
        sbi.asset_collection.to_id_file(f"{platform._config_block}_my_shiny_new_idm_test.id")
        print("ac_obj: ", ac_obj.id)
        get_files(sbi.id, "my_shiny_new_idm_test.sif")