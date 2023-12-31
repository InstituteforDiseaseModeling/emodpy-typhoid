# Blantyre Scenario & Workflow

## Purpose

The goal of this example is to recreate: https://github.com/InstituteforDiseaseModeling/ESEcon

But without the enviro surveillance part.

Some highlights of the ESEcon scenario:
- Base_Year: 1970
- Duration: 30 Years
- Seasonality: [Trapezoid](https://github.com/MIzzo-IDM/EMOD-docs/blob/master/emod/images/Typhoid/enviro-amplification3.PNG)
    - Typhoid_Environmental_Cutoff_Days: 18.8
    - Typhoid_Environmental_Peak_Start: 290
    - Typhoid_Environmental_Ramp_Down_Duration: 227.7
    - Typhoid_Environmental_Ramp_Up_Duration: 11.5

- Campaign: ...
    - Outbreak/Seeding: 1(x5/_730) :: AllPlaces :: 0.25% :: OutbreakIndividual
    - Vaccines: TBD
- Demographics:
    - Initial Age: exponential.
    - Fertility: Highly configured, declining from 1950 to 2015
    - Natural Mortality: Highly configured, 1950 to 2015
    - HINT groups: 8. Contact is entirely intragroup. Enviro is a linear chain.


The COMPS run of this is here:

https://comps.idmod.org/#explore/Simulations?filters=ExperimentId=1b1a1c02-5c97-e911-a2c1-c4346bcb1555&offset=0&count=100&selectedId=e2670e14-5c97-e911-a2c1-c4346bcb1555&mode=list&resizer=502C502C0

Except there are some differences (TBD).

Some notes on the COMPS version:
- The COMPS run goes from 1917 to 2039
- There is a t=1 seeding of 50% and 10 years of annual 0.5% seeding.
- Typhoid Vaccines are introduced in 2017 (100 years in) to 85% of 9-month-olds.
- The initial age is exponential.
- The fertility is "high" fro 1917 to 1960, then goes down to a low modern value.
- Mortality is realistic for early years and constant across the sim.
- The net population has a nice realistic "sigmod" pattern with cresting in near future.
- The prevalence is low and steadily rising across the latter part of the sim.
