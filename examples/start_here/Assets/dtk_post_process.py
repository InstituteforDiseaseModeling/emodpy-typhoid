import json
import os

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from datetime import datetime, timedelta
from dateutil import relativedelta

def get_archetype_name():
    with open("config.json", 'r') as f:
        d = json.load(f)
    return d["archetype"]

def summarize_infection():
    # Summarize endpoint
    event_recorder_filepath = os.path.join("output", "InsetChart.json")
    with open(event_recorder_filepath, 'r') as f:
        d = json.load(f)

    endpoint_data = {
        "infected": np.mean(np.array(d["Channels"]["Infected"]["Data"])[-365:]),
        "new_infected": np.mean(np.array(d["Channels"]["New Infections"]["Data"])[-365:])
    }

    json.dump(endpoint_data, open(os.path.join("output", "infected.json"), 'w'))

def population():
    insetchart_path = os.path.join("output", "InsetChart.json")
    with open(insetchart_path, 'r') as f:
        data = json.load(f)

    population = data["Channels"]["Statistical Population"]["Data"]
    timesteps = list(range(data["Header"]["Timesteps"]))
    # Package into a dictionary
    output = {
        "timesteps": timesteps,
        "population": population
    }

    # Save to JSON file
    with open(os.path.join("output", "population.json"), "w") as f:
        json.dump(output, f, indent=2)

def plot_newly_infected():
    with open(os.path.join("output", "InsetChart.json"), "r") as f:
        data = json.load(f)

    # Extract data
    timesteps = list(range(data["Header"]["Timesteps"]))
    infected = data["Channels"]["Infected"]["Data"]
    new_infections = data["Channels"]["New Infections"]["Data"]

    # Plot Infected Fraction and save
    plt.figure(figsize=(12, 5))
    plt.plot(timesteps, infected, label="Infected Fraction")
    plt.xlabel("Timestep")
    plt.ylabel("Fraction")
    plt.title("Infected Fraction vs Time")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig("infected_fraction_vs_time.png", dpi=300)  # Save plot
    plt.show()

    # Plot New Infections and save
    plt.figure(figsize=(12, 5))
    plt.plot(timesteps, new_infections, color="orange", label="New Infections")
    plt.xlabel("Timestep")
    plt.ylabel("Count")
    plt.title("New Infections vs Time")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig("new_infections_vs_time.png", dpi=300)  # Save plot
    plt.show()

def application(output_folder="output"):
    print("starting dtk post process!")

    summarize_infection()
    plot_newly_infected()
    population()


if __name__ == "__main__":
    # Placeholder for now
    application(output_folder="output")
    # application(output_folder='.') #for testing