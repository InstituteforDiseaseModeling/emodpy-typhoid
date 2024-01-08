import os
current_dir = os.path.dirname(__file__)
requirements = "./requirements.txt"
model_dl_dir = "stash"
schema_file=os.path.join(model_dl_dir, "schema.json")
eradication_path=os.path.join(model_dl_dir, "Eradication")
assets_input_dir=os.path.join(current_dir,"Assets")
reporters=model_dl_dir
sif=os.path.join(current_dir,"dtk_centos_2018_stage.id")
world_bank_dataset=os.path.join(current_dir, "../../examples/world_bank_dataset.csv")
