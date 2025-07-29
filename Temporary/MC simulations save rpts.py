import os
import pandas as pd
import datetime
from swmm_api.input_file import SwmmInput
from swmm_api.input_file.sections.lid import LIDUsage
from swmm_api import read_rpt_file
from pyswmm import Simulation, Nodes
import numpy as np

# File paths
csv_file_path = r"C:\Users\ABI\My_Files\MonteCarlo\filtered_random_LID_data_with_trees.csv"
input_file = r"C:\Users\ABI\My_Files\MonteCarlo\SWMMFiles\Loren_singleblock_LT_perv_imperv_withouttrees.inp"
temp_inp = r"C:\Users\ABI\My_Files\MonteCarlo\SWMMFiles\model_temp.inp"
temp_rpt = temp_inp.replace(".inp", ".rpt")
results_dir = r"C:\Users\ABI\My_Files\MonteCarlo\Results"
rpt_save_dir = r"C:\Users\ABI\My_Files\MonteCarlo\Results_WQ"  # Store .rpt files for later
os.makedirs(results_dir, exist_ok=True)
os.makedirs(rpt_save_dir, exist_ok=True)

# Constants
yr_start, yr_stop = 1968, 2023

# Load LID parameter combinations
df = pd.read_csv(csv_file_path, delimiter=";")

# Loop over simulations
for sim_number in range(len(df)):
    row_data = df.iloc[sim_number]
    inp = SwmmInput(input_file)

    # Add LIDs for roof areas (S1–S4)
    for i in range(1, 5):
        sub = f"S{i}"
        lid_area = row_data[sub]
        lid_type = row_data["Type"]
        if lid_area > 0:
            inp["LID_USAGE"][(sub, lid_type)] = LIDUsage(
                subcatchment=sub,
                lid=lid_type,
                n_replicate=1,
                area=lid_area,
                width=10,
                saturation_init=0.0,
                impervious_portion=100.0,
                route_to_pervious=0.0,
                fn_lid_report='*',
                drain_to='*',
                from_pervious=0.0
            )

    # Add LIDs for terrain subcatchments (S5, S7–S11) except trees
    for i in [5, 7, 8, 9, 10, 11]:
        sub = f"S{i}"
        lid_area = row_data[sub]
        lid_type = row_data[f"{sub}_Type"]
        if lid_area > 0 and lid_type != 'TRE':
            inp["LID_USAGE"][(sub, lid_type)] = LIDUsage(
                subcatchment=sub,
                lid=lid_type,
                n_replicate=1,
                area=lid_area,
                width=10,
                saturation_init=0.0,
                impervious_portion=100.0,
                route_to_pervious=0.0,
                fn_lid_report='*',
                drain_to='*',
                from_pervious=0.0
            )

    results = []

    for year in range(yr_start, yr_stop + 1):
        sim_start = datetime.date(year, 5, 1)
        sim_end = datetime.date(year, 10, 31)

        # Set simulation period
        inp.OPTIONS['START_DATE'] = sim_start
        inp.OPTIONS['END_DATE'] = sim_end
        inp.OPTIONS['REPORT_START_DATE'] = sim_start
        inp.write_file(temp_inp)

        print(f"Simulating year {year} for scenario {sim_number}...")

        inflows = []
        timestamps = []

        with Simulation(temp_inp) as sim:
            node = Nodes(sim)["O"]
            for step in sim:
                inflows.append(node.total_inflow)
                timestamps.append(sim.current_time)

        sim_q = np.array(inflows)
        peak_flow = round(sim_q.max(), 3)
        peak_index = sim_q.argmax()
        peak_time = timestamps[peak_index]
        total_volume = round(sim_q.sum() * 60, 3)  # m3 assuming timestep is 60s

        # Save .rpt file for this year
        rpt_path = os.path.join(rpt_save_dir, f"rpt_sim{sim_number}_year{year}.rpt")
        os.replace(temp_rpt, rpt_path)
        rpt = read_rpt_file(rpt_path)

        # Extract hydrology continuity metrics
        cont = rpt.runoff_quantity_continuity
        PRE = cont['Total Precipitation']['Depth_mm']
        EVA = cont['Evaporation Loss']['Depth_mm']
        INF = cont['Infiltration Loss']['Depth_mm']
        PHI = round((PRE - EVA - INF) / PRE, 2) if PRE > 0 else 0

        results.append({
            'YEAR': year,
            'PR': peak_flow,
            't_PR': peak_time,
            'TR': total_volume,
            'PRE': round(PRE, 2),
            'EVA': round(EVA, 2),
            'INF': round(INF, 2),
            'PHI': PHI,
        })

    # Save hydrology results for this simulation
    df_out = pd.DataFrame(results)
    df_out.to_csv(os.path.join(results_dir, f"swmm_MC_results{sim_number}.csv"), index=False, sep=';')

    print(f"Simulation {sim_number} completed and saved.")
