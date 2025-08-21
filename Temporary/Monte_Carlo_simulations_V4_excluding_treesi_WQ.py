import os
import pandas as pd
import datetime
from swmm_api.input_file import SwmmInput
from swmm_api.input_file.sections.lid import LIDUsage
from swmm_api import read_rpt_file
from pyswmm import Simulation, Nodes
import numpy as np

# Paths
csv_file_path = r"C:\Users\ABI\OneDrive - NIVA\Documents\GitHub\SWMM_MOO\01_Preprocessing\filtered_random_LID_data_with_trees.csv"
input_file = r"C:\Users\ABI\My_Files\MonteCarlo\SWMMFiles\Loren_singleblock_LT_perv_imperv_withouttrees.inp"
base_name = os.path.basename(input_file).replace(".inp", "")
temp_inp = r"C:\Users\ABI\My_Files\MonteCarlo\SWMMFiles\model_temp.inp"
temp_rpt = temp_inp.replace(".inp", ".rpt")
results_dir = r"C:\Users\ABI\My_Files\MonteCarlo\Results"
results_wq = r"C:\Users\ABI\My_Files\MonteCarlo\Results_WQ"


# Constants
yr_start, yr_stop = 1968, 2023

# Load CSV data
df = pd.read_csv(csv_file_path, delimiter=";")

for sim_number in range(0, 1):
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
        # new_imperv_area = row_data[f"{sub}_Aimp"]
        # total_area = inp.SUBCATCHMENTS[sub].area 
        # new_imperv_percent = (new_imperv_area / (total_area * 10000)) * 100
        # inp.SUBCATCHMENTS[sub].imperviousness = round(new_imperv_percent, 2)
        
        
        if lid_area > 0 and lid_type != 'TRE':                          # This parts skips adding of trees into the model
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
    lid_flow_results =[]
    
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
        PR = peak_flow
        TR = total_volume
        
        rpt = read_rpt_file(temp_rpt)
        PRE = rpt.runoff_quantity_continuity['Total Precipitation']['Depth_mm']
        EVA = rpt.runoff_quantity_continuity['Evaporation Loss']['Depth_mm']
        INF = rpt.runoff_quantity_continuity['Infiltration Loss']['Depth_mm']
        PHI = round((PRE - EVA - INF) / PRE, 2) if PRE > 0 else 0
        
        
        

        results.append({
            'YEAR': year,
            'PR': PR,
            't_PR': peak_time,
            'TR': total_volume,
            'PRE': round(PRE, 2),
            'EVA': round(EVA, 2),
            'INF': round(INF, 2),
            'PHI': PHI,
            
        })
        
        ## Extract flow values for water quality calculations
        
        gr_drain = []
        bc_outflow =[]
        bc_drain = []
        gs_outflow = []
        
        rpt_lid = rpt.lid_performance_summary
        if rpt_lid is not None:
            for i in range(1, 5):
                sub = f"S{i}"
                if sub in rpt_lid.index:
                    gr_drain.append(rpt_lid['Surface_Outflow_mm'].loc[sub])
            
            for i in [5, 7, 8, 9, 10, 11]:
                sub = f"S{i}"
                if sub in rpt_lid.index:
                    if rpt_lid['LID'].loc[sub] == 'BC':
                        bc_outflow.append(rpt_lid['Infil_Loss_mm'].loc[sub])
                        bc_drain.append(rpt_lid['Surface_Outflow_mm'].loc[sub])
                    else:
                        gs_outflow.append(rpt_lid['Infil_Loss_mm'].loc[sub])

       # Summing flow values for water quality calculations
        gr_drain_total = round(sum(gr_drain), 3)
        bc_outflow_total = round(sum(bc_outflow), 3)
        bc_drain_total = round(sum(bc_drain), 3)
        gs_outflow_total = round(sum(gs_outflow), 3)
        
        # Append to water quality results
        lid_flow_results.append({
            'YEAR': year,
            'GR_DRAIN': gr_drain_total,
            'BC_Outflow': bc_outflow_total,
            'BC_Drain': bc_drain_total,
            'GS_Outflow': gs_outflow_total
        })        
            

    results_df = pd.DataFrame(results)
    results_df.to_csv(
        os.path.join(results_dir, f"swmm_MC_results{sim_number}.csv"),
        index=False,
        sep=';'
    )
    
    # Compute average LID flow metrics over all years for this simulation
    lid_flow_results_df = pd.DataFrame(lid_flow_results)
    avg_lid_flows = lid_flow_results_df[['GR_DRAIN', 'BC_Outflow', 'BC_Drain', 'GS_Outflow']].mean().round(3)
    avg_lid_flows['Sim'] = sim_number  # Tag simulation number
    
    # # Append to master file (all simulations)
    # summary_csv_path = os.path.join(r'C:\Users\ABI\My_Files\MonteCarlo', "swmm_MC_flow_summary_avg.csv")
    
    #     # If the summary file already exists, append to it; else, create it
    # if os.path.exists(summary_csv_path):
    #     existing_df = pd.read_csv(summary_csv_path, sep=';')
    #     updated_df = pd.concat([existing_df, pd.DataFrame([avg_lid_flows])], ignore_index=True)
    # else:
    #     updated_df = pd.DataFrame([avg_lid_flows])

    # # Save the updated summary file
    # updated_df.to_csv(summary_csv_path, index=False, sep=';')
    # print(f"Simulation {sim_number} completed and saved.")
    
