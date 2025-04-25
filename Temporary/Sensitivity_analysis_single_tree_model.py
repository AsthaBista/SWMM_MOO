# -*- coding: utf-8 -*-
"""
Created on Tue Apr  1 09:52:34 2025

@author: ABI
"""
import pandas as pd
from swmm_api.input_file import SwmmInput
from pyswmm import Simulation
from swmm_api import read_rpt_file



input_file = r"C:\Users\ABI\OneDrive - NIVA\PhD_Work\Work\PartII\Loren\SWMM_MOO\SWMMFiles\Single_tree_model.inp"
inp = SwmmInput(input_file)
temp_file = r'C:\Users\ABI\OneDrive - NIVA\PhD_Work\Work\PartII\Loren\SWMM_MOO\SWMMFiles\singletree_temp.inp'

results = []
for i, j in zip(range(1, 5), [5, 7, 12, 15]):
    berm_height = j
    inp.LID_CONTROLS['TRE'].layer_dict['SURFACE'].StorHt = berm_height
    
    inp.write_file(temp_file)
    
    print(f"Running scenario {i}...")
    with Simulation(temp_file) as sim:
            for step in sim:
                pass

    rpt = read_rpt_file(r"C:\Users\ABI\OneDrive - NIVA\PhD_Work\Work\PartII\Loren\SWMM_MOO\SWMMFiles\singletree_temp.rpt")
    PRE = rpt.runoff_quantity_continuity['Total Precipitation']['Depth_mm']
    EVA = rpt.runoff_quantity_continuity['Evaporation Loss']['Depth_mm']
    INF = rpt.runoff_quantity_continuity['Infiltration Loss']['Depth_mm']
    PHI = round((PRE - EVA - INF) / PRE, 2) if PRE > 0 else 0
    
    results.append({
        'SIM': i,
        'Berm_height': berm_height,
        'PRE': round(PRE, 2),
        'EVA': round(EVA, 2),
        'INF': round(INF, 2),
        'PHI': PHI
    })
    
results_df = pd.DataFrame(results)
results_df.to_csv(r"C:\Users\ABI\OneDrive - NIVA\PhD_Work\Work\PartII\Loren\SWMM_MOO\SWMMFiles\singletree_results.csv", sep =';')


# import matplotlib.pyplot as plt
# import seaborn as sns

# # Optional: If you're running this as a separate script
# # results_df = pd.read_csv("path_to_your_csv.csv", sep=';')

# # Set seaborn style for nicer plots
# sns.set(style='whitegrid')

# # Plot 1: Berm Height vs Total Interception
# results_df['INTERCEPTION'] = results_df['EVA'] + results_df['INF']

# plt.figure(figsize=(10, 6))
# sns.lineplot(x='Berm_height', y='INTERCEPTION', data=results_df, marker='o')
# plt.title("Total Interception (EVA + INF) vs Berm Height")
# plt.xlabel("Berm Height (mm)")
# plt.ylabel("Interception (mm)")
# plt.tight_layout()
# plt.show()

# # Plot 2: Berm Height vs Each Component
# plt.figure(figsize=(10, 6))
# sns.lineplot(x='Berm_height', y='EVA', data=results_df, label='Evaporation Loss', marker='o')
# sns.lineplot(x='Berm_height', y='INF', data=results_df, label='Infiltration Loss', marker='o')
# plt.title("Evaporation & Infiltration vs Berm Height")
# plt.xlabel("Berm Height (mm)")
# plt.ylabel("Depth (mm)")
# plt.legend()
# plt.tight_layout()
# plt.show()

