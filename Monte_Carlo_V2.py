import os
import pandas as pd
import datetime
from swmm_api.input_file import SwmmInput
from swmm_api.input_file.sections.lid import LIDUsage
from swmm_api import read_rpt_file
from pyswmm import Simulation, Nodes
import numpy as np

# Paths
csv_file_path = r"C:\Users\ABI\My_Files\MonteCarlo\filtered_random_LID_data_with_trees.csv"
input_file = r"C:\Users\ABI\My_Files\MonteCarlo\SWMMFiles\Loren_singleblock_LT_perv_imperv.inp"
base_name = os.path.basename(input_file).replace(".inp", "")
temp_inp = r"C:\Users\ABI\My_Files\MonteCarlo\SWMMFiles\model_temp.inp"
temp_rpt = temp_inp.replace(".inp", ".rpt")
results_dir = r"C:\Users\ABI\My_Files\MonteCarlo\Results"

# Constants
yr_start, yr_stop = 1968, 2023

# Load CSV data
df = pd.read_csv(csv_file_path, delimiter=";")

for sim_number in range(0, 2):
    row_data = df.iloc[sim_number]
    inp = SwmmInput(input_file)

    # Update LID usage for S1–S4 (roof areas)
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

    # Update LID usage for terrain subcatchments
    for i in [5, 7, 8, 9, 10, 11]:
        sub = f"S{i}"
        lid_area = row_data[sub]
        lid_type = row_data[f"{sub}_Type"]
        new_area = row_data[f"{sub}_Aimp"]
        inp.SUBCATCHMENTS[sub].area = round(new_area * 0.0001, 4)
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

    results = []

    for year in range(yr_start, yr_stop + 1):
        sim_start = datetime.date(year, 5, 1)
        sim_end = datetime.date(year, 10, 31)
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
        total_volume = round(sim_q.sum() * 60, 3)

        rpt = read_rpt_file(temp_rpt)
        PRE = rpt.runoff_quantity_continuity['Total Precipitation']['Depth_mm']
        EVA = rpt.runoff_quantity_continuity['Evaporation Loss']['Depth_mm']
        INF = rpt.runoff_quantity_continuity['Infiltration Loss']['Depth_mm']
        PHI = round((PRE - EVA - INF) / PRE, 2) if PRE > 0 else 0

        results.append({
            'YEAR': year,
            'PR': peak_flow,
            't_PR': peak_time,
            'TR': total_volume,
            'PRE': round(PRE, 2),
            'EVA': round(EVA, 2),
            'INF': round(INF, 2),
            'PHI': PHI
        })

    results_df = pd.DataFrame(results)
    results_df.to_csv(
        os.path.join(results_dir, f"swmm_MC_results{sim_number}.csv"),
        index=False,
        sep=';'
    )

    print(f"Simulation {sim_number} completed and saved.")
