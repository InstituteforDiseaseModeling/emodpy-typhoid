import json
import os

import pandas as pd
from idmtools.entities.ianalyzer import BaseAnalyzer
from matplotlib import pyplot as plt


class PopulationAnalyzer(BaseAnalyzer):

    def __init__(self, output_path="output", filenames=["output/population.json"]):
        super().__init__(filenames=filenames)
        self.output_path = output_path

    def filter(self, simulation) -> bool:
        return int(simulation.tags.get("Run_Number")) > 2

    # idmtools analyzer
    def map(self, data, simulation):
        return data[self.filenames[0]]

    def reduce(self, all_data: dict):
        first_sim = list(all_data.keys())[0]  # get first Simulation
        exp_id = first_sim.experiment.id  # Set the exp id from the first sim data
        output_folder = os.path.join(self.output_path, exp_id)
        os.makedirs(output_folder, exist_ok=True)

        data = {str(s.uid): v for s, v in all_data.items()}
        with open(os.path.join(output_folder, "total_population.json"), "w") as fp:
            json.dump(data, fp)

        # Reconstruct the same dictionary structure from your `all_data`


        # Extract all unique timesteps
        all_timesteps = set()
        for v in data.values():
            all_timesteps.update(v["timesteps"])
        sorted_timesteps = sorted(all_timesteps)

        # Initialize a DataFrame with timesteps
        df = pd.DataFrame({"timestep": sorted_timesteps})

        # Add each simulation's population as a column
        for sim_uid, v in data.items():
            series = pd.Series(v["population"], index=v["timesteps"])
            df[sim_uid] = series.reindex(sorted_timesteps).values

        # Save to CSV
        csv_path = os.path.join(output_folder, "total_population.csv")
        df.to_csv(csv_path, index=False)

        plt.figure(figsize=(12, 6))

        for run_id, content in all_data.items():
            timesteps = content["timesteps"]
            population = content["population"]
            plt.plot(timesteps, population, label=run_id.id)  # Use partial ID for cleaner legend

        plt.xlabel("Timestep")
        plt.ylabel("Population")
        plt.title("Population over Time for Each Run")
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.savefig("population_vs_time_by_run.png", dpi=300)
        plt.show()