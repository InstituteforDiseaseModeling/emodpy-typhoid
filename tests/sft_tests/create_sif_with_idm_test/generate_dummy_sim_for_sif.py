import os

from idmtools.assets import AssetCollection
from idmtools.core.platform_factory import Platform
from idmtools.entities import CommandLine
from idmtools.entities.command_task import CommandTask
from idmtools.entities.experiment import Experiment

with Platform("SlurmStage") as platform:
    ac = AssetCollection.from_id_file("SlurmStage_my_shiny_new_idm_test.id")
    result = platform.create_items(ac)
    print(result[0].id)

    # option code to keep ac in system
    command = CommandLine("singularity exec ./Assets/my_shiny_new_idm_test.sif python3 --version")
    task = CommandTask(command=command)
    task.common_assets.add_assets(AssetCollection.from_id(result[0].id))
    experiment = Experiment.from_task(
        task,
        name="generate sif ac",
        tags=dict(type='singularity', description='run test', sif_ac=result[0].id)
    )
    experiment.run(wait_until_done=True)
