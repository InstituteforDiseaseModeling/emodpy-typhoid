import os
requirements = "./requirements.txt"
model_dl_dir = "stash"
schema_file=os.path.join(model_dl_dir, "schema.json")
eradication_path=os.path.join(model_dl_dir, "Eradication")
assets_input_dir="Assets"
reporters=model_dl_dir
sif='rocky_runner_extra.sif.id'
world_bank_dataset="../world_bank_dataset.csv"
base_folder = os.path.dirname(os.path.realpath(__file__))
ep4_path = os.path.join(base_folder, "Assets")
