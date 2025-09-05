######################################################
######            1. IMPORTERER PAKKER          ######
######################################################

import pandas as pd
from swmm_api import read_inp_file, SwmmInput
from pyswmm import Simulation
import matplotlib.pyplot as plt
import time
import openpyxl
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.optimize import minimize
import numpy as np
from pymoo.core.problem import ElementwiseProblem
from swmm_functions import calculate_annual_runoff_volume
import copy

# Start the time
start_time = time.time()

######################################################
######            2. Input Values          ######
######################################################
# There are four roof subcatchments S1, S2, S3, S4, and the rest S5...S11 are terrain subcatchments
# For roofs, when green roofs are applied, they cover the whole roof
# For terrains, measures (bioretention cells, grassed areas, and trees) 
# cover a certain percentage of the total area.
# In this case, a 15% of total subcatchment area limit is applied for terrain LIDs.
# This has been added as a constraint, so solutions that violate this limit is penalized, 
# and eventually the algorithm avoids these violated solutions.

infiltrasjonsrate = 50 # lokal infiltrasjonsrate [mm/t]

a_S1 = 939        # areal i delfelt [m2]
a_S2 = 494        # areal i delfelt [m2]
a_S3 = 506        # areal i delfelt [m2]
a_S4 = 921        # areal i delfelt [m2]
a_S5 = 340        # areal i delfelt [m2]
a_S6 = 1113       # areal i delfelt [m2]
a_S7 = 285        # areal i delfelt [m2]
a_S8 = 415        # areal i delfelt [m2]
a_S9 = 422        # areal i delfelt [m2]
a_S10 = 447       # areal i delfelt [m2]
a_S11 = 390       # areal i delfelt [m2]

r_dis = 0.04       # discount rate
n_per = 50         # lifespan

population = 5   # population for NSGA-II
generation = 3  # generations for NSGA-II

######################################################
#######      3. Preparation for Calculations    ######
######################################################
#
base_inp = read_inp_file(r"C:\Users\ABI\My_Files\MonteCarlo\SWMMFiles\Loren_singleblock_for_MOO.inp")
inp = copy.deepcopy(base_inp)

# Set the areas into inp file in each subcatchment                    
inp.SUBCATCHMENTS['S1'].area = a_S1/10000
inp.SUBCATCHMENTS['S2'].area = a_S2/10000
inp.SUBCATCHMENTS['S3'].area = a_S3/10000
inp.SUBCATCHMENTS['S4'].area = a_S4/10000
inp.SUBCATCHMENTS['S5'].area = a_S5/10000
inp.SUBCATCHMENTS['S6'].area = a_S6/10000
inp.SUBCATCHMENTS['S7'].area = a_S7/10000
inp.SUBCATCHMENTS['S8'].area = a_S8/10000
inp.SUBCATCHMENTS['S9'].area = a_S9/10000
inp.SUBCATCHMENTS['S10'].area = a_S10/10000
inp.SUBCATCHMENTS['S11'].area = a_S11/10000

# Enter the unit values for the objectives
BGF_gr5 =  0.3
BGF_gr20 = 0.5
BGF_bc = 3
BGF_gs = 1
BGF_tre = 30

inp.write_file(r"C:\Users\ABI\My_Files\MonteCarlo\SWMMFiles\Loren_singleblock_for_MOO.inp")

# Get the areas from the inp file
a_S1 = inp.SUBCATCHMENTS['S1'].area*10000
a_S2 = inp.SUBCATCHMENTS['S2'].area*10000
a_S3 = inp.SUBCATCHMENTS['S3'].area*10000
a_S4 = inp.SUBCATCHMENTS['S4'].area*10000
a_S5 = inp.SUBCATCHMENTS['S5'].area*10000
a_S6 = inp.SUBCATCHMENTS['S6'].area*10000
a_S7 = inp.SUBCATCHMENTS['S7'].area*10000
a_S8 = inp.SUBCATCHMENTS['S8'].area*10000
a_S9 = inp.SUBCATCHMENTS['S9'].area*10000
a_S10 = inp.SUBCATCHMENTS['S10'].area*10000
a_S11 = inp.SUBCATCHMENTS['S11'].area*10000

######################################################
#######      3. HELPER FUNCTIONS                ######
######################################################

# Function to calculate total BGF area based on LID implementations
def calculate_total_bgf_area(x):
    """
    Calculate total BGF area based on LID implementations
    """
    total_bgf_area = 0
    
    # Roof areas (S1-S4)
    roof_areas = [a_S1, a_S2, a_S3, a_S4]
    
    for i in range(4):
        r_type = int(x[i] * 3) + 1
        
        if r_type == 1:  # GR5
            total_bgf_area += roof_areas[i]
        elif r_type == 2:  # GR20
            total_bgf_area += roof_areas[i]
    
    # Terrain areas (S5, S7-S11)
    terrain_areas = [a_S5, a_S7, a_S8, a_S9, a_S10, a_S11]
    terrain_indices = [4, 6, 8, 10, 12, 14]
    area_ratio_indices = [5, 7, 9, 11, 13, 15]
    
    for i in range(6):
        t_type = int(x[terrain_indices[i]] * 4) + 1
        area_ratio = x[area_ratio_indices[i]]
        lid_area = terrain_areas[i] * area_ratio
        
        if t_type == 1:  # BC
            total_bgf_area += lid_area
        elif t_type == 2:  # GS
            total_bgf_area += lid_area
        elif t_type == 3:  # TRE
            total_bgf_area += lid_area
    
    return total_bgf_area

# Returns impervious percentage (0–100) for a given subcatchment ID
def _imp_pct(sub_id):
    # swmm_api stores the field in SUBCATCHMENTS[sub_id].data['pct_imperv']
    return float(inp.SUBCATCHMENTS[sub_id].data.get('pct_imperv', 0.0))

# Computes tree counts for a terrain subcatchment
# - Effective canopy area per tree = 7 m²
# - Maximum allowed tree coverage = 15% of subcatchment area
# - Trees on impervious area are proportional to impervious fraction
def _trees_for_sub(a_tot, r_frac, sub_id):
    # Requested tree coverage from decision variable
    wish_area = a_tot * r_frac
    # Enforce 15% cap
    cap_area = 0.15 * a_tot
    eff_area = min(wish_area, cap_area)
    # Total trees based on effective canopy area
    total_trees = int(round(eff_area / 7.0))
    # Split by impervious fraction
    imp_frac = _imp_pct(sub_id) / 100.0
    imp_trees = int(round(total_trees * imp_frac))
    return total_trees, imp_trees

# Local setup_lid_usage function
from swmm_api.input_file import SwmmInput
from swmm_api.input_file.sections.lid import LIDUsage


def setup_lid_usage(inp, subcatchment, lid_type, area, impervious_portion=100.0):
    """
    Add/replace a LID usage row for (subcatchment, lid_type).
    Removes it when area <= 0.
    """
    key = (subcatchment, lid_type)

    # Remove old entry (if any)
    if key in inp.LID_USAGE:
        del inp.LID_USAGE[key]

    # Only add a new row if we actually have area
    if area > 0:
        lu = LIDUsage(
            subcatchment=subcatchment,
            lid=lid_type,          # must match a name in LID_CONTROLS
            n_replicate=1,
            area=float(area),      # m²
            width=10.0,            # pick something sensible for your site
            saturation_init=0.0,   # field names match your current version
            impervious_portion=float(impervious_portion),
            route_to_pervious=0.0,
            fn_lid_report="*",
            drain_to="*",
            from_pervious=0.0,
        )
        inp.LID_USAGE[lu.key] = lu
############################################################
########  4. DEFINE THE PROBLEM FOR OPTIMIZATION #####
############################################################

class MyProblem(ElementwiseProblem):

    def __init__(self):
        super().__init__(n_var=16,                                   # number of variables
                         n_obj=2,                                    # number of objectives
                         n_ieq_constr=6,                             # 6 constraints for terrain areas
                         xl=np.array([0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]),     # lower bounds for variables
                         xu=np.array([1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]))     # upper bounds for variables
    
    def _evaluate(self, x, out, *args, **kwargs):
        # Initialize tree counters
        trees_tot = 0
        trees_imp = 0
        
        # Now, assigning NbS measures types and sizes to subcatchments:
    
        #############
        #### ROOF ####
        #############
    
       #### S1 ####
        r1 = int(x[0] * 3) + 1
        if r1 == 1:
            setup_lid_usage(inp, 'S1', 'GR5', a_S1, 100.0)
            setup_lid_usage(inp, 'S1', 'GR20', 0, 0.0)
        elif r1 == 2:
            setup_lid_usage(inp, 'S1', 'GR5', 0, 0.0)
            setup_lid_usage(inp, 'S1', 'GR20', a_S1, 100.0)
        else:
            setup_lid_usage(inp, 'S1', 'GR5', 0, 0.0)
            setup_lid_usage(inp, 'S1', 'GR20', 0, 0.0)
        
        #### S2 ####
        r2 = int(x[1] * 3) + 1
        if r2 == 1:
            setup_lid_usage(inp, 'S2', 'GR5', a_S2, 100.0)
            setup_lid_usage(inp, 'S2', 'GR20', 0, 0.0)
        elif r2 == 2:
            setup_lid_usage(inp, 'S2', 'GR5', 0, 0.0)
            setup_lid_usage(inp, 'S2', 'GR20', a_S2, 100.0)
        else:
            setup_lid_usage(inp, 'S2', 'GR5', 0, 0.0)
            setup_lid_usage(inp, 'S2', 'GR20', 0, 0.0)
        
        #### S3 ####
        r3 = int(x[2] * 3) + 1
        if r3 == 1:
            setup_lid_usage(inp, 'S3', 'GR5', a_S3, 100.0)
            setup_lid_usage(inp, 'S3', 'GR20', 0, 0.0)
        elif r3 == 2:
            setup_lid_usage(inp, 'S3', 'GR5', 0, 0.0)
            setup_lid_usage(inp, 'S3', 'GR20', a_S3, 100.0)
        else:
            setup_lid_usage(inp, 'S3', 'GR5', 0, 0.0)
            setup_lid_usage(inp, 'S3', 'GR20', 0, 0.0)
        
        #### S4 ####
        r4 = int(x[3] * 3) + 1
        if r4 == 1:
            setup_lid_usage(inp, 'S4', 'GR5', a_S4, 100.0)
            setup_lid_usage(inp, 'S4', 'GR20', 0, 0.0)
        elif r4 == 2:
            setup_lid_usage(inp, 'S4', 'GR5', 0, 0.0)
            setup_lid_usage(inp, 'S4', 'GR20', a_S4, 100.0)
        else:
            setup_lid_usage(inp, 'S4', 'GR5', 0, 0.0)
            setup_lid_usage(inp, 'S4', 'GR20', 0, 0.0)
        
        #### S5 ####
        r5 = int(x[4] * 4) + 1
        ra5 = x[5]
        
        if r5 == 1:
            setup_lid_usage(inp, 'S5', 'BC', round(a_S5 * ra5, 0), 100.0)
            setup_lid_usage(inp, 'S5', 'GS', 0, 0.0)
        elif r5 == 2:
            setup_lid_usage(inp, 'S5', 'BC', 0, 0.0)
            setup_lid_usage(inp, 'S5', 'GS', round(a_S5 * ra5, 0), 100.0)
        elif r5 == 3:  # TRE is handled outside of SWMM
            setup_lid_usage(inp, 'S5', 'BC', 0, 0.0)
            setup_lid_usage(inp, 'S5', 'GS', 0, 0.0)
            t_total, t_imp = _trees_for_sub(a_S5, ra5, 'S5')
            trees_tot += t_total
            trees_imp += t_imp
        else:
            setup_lid_usage(inp, 'S5', 'BC', 0, 0.0)
            setup_lid_usage(inp, 'S5', 'GS', 0, 0.0)
        
        #### S7 ####
        r6 = int(x[6] * 4) + 1
        ra6 = x[7]
        
        if r6 == 1:
            setup_lid_usage(inp, 'S7', 'BC', round(a_S7 * ra6, 0), 100.0)
            setup_lid_usage(inp, 'S7', 'GS', 0, 0.0)
        elif r6 == 2:
            setup_lid_usage(inp, 'S7', 'BC', 0, 0.0)
            setup_lid_usage(inp, 'S7', 'GS', round(a_S7 * ra6, 0), 100.0)
        elif r6 == 3:  # TRE is handled outside of SWMM
            setup_lid_usage(inp, 'S7', 'BC', 0, 0.0)
            setup_lid_usage(inp, 'S7', 'GS', 0, 0.0)
            t_total, t_imp = _trees_for_sub(a_S7, ra6, 'S7')
            trees_tot += t_total
            trees_imp += t_imp
        else:
            setup_lid_usage(inp, 'S7', 'BC', 0, 0.0)
            setup_lid_usage(inp, 'S7', 'GS', 0, 0.0)
        
        #### S8 ####
        r7 = int(x[8] * 4) + 1
        ra7 = x[9]
        
        if r7 == 1:
            setup_lid_usage(inp, 'S8', 'BC', round(a_S8 * ra7, 0), 100.0)
            setup_lid_usage(inp, 'S8', 'GS', 0, 0.0)
        elif r7 == 2:
            setup_lid_usage(inp, 'S8', 'BC', 0, 0.0)
            setup_lid_usage(inp, 'S8', 'GS', round(a_S8 * ra7, 0), 100.0)
        elif r7 == 3:  # TRE is handled outside of SWMM
            setup_lid_usage(inp, 'S8', 'BC', 0, 0.0)
            setup_lid_usage(inp, 'S8', 'GS', 0, 0.0)
            t_total, t_imp = _trees_for_sub(a_S8, ra7, 'S8')
            trees_tot += t_total
            trees_imp += t_imp
        else:
            setup_lid_usage(inp, 'S8', 'BC', 0, 0.0)
            setup_lid_usage(inp, 'S8', 'GS', 0, 0.0)
        
        #### S9 ####
        r8 = int(x[10] * 4) + 1
        ra8 = x[11]
        
        if r8 == 1:
            setup_lid_usage(inp, 'S9', 'BC', round(a_S9 * ra8, 0), 100.0)
            setup_lid_usage(inp, 'S9', 'GS', 0, 0.0)
        elif r8 == 2:
            setup_lid_usage(inp, 'S9', 'BC', 0, 0.0)
            setup_lid_usage(inp, 'S9', 'GS', round(a_S9 * ra8, 0), 100.0)
        elif r8 == 3:  # TRE is handled outside of SWMM
            setup_lid_usage(inp, 'S9', 'BC', 0, 0.0)
            setup_lid_usage(inp, 'S9', 'GS', 0, 0.0)
            t_total, t_imp = _trees_for_sub(a_S9, ra8, 'S9')
            trees_tot += t_total
            trees_imp += t_imp
        else:
            setup_lid_usage(inp, 'S9', 'BC', 0, 0.0)
            setup_lid_usage(inp, 'S9', 'GS', 0, 0.0)
        
        #### S10 ####
        r9 = int(x[12] * 4) + 1
        ra9 = x[13]
        
        if r9 == 1:
            setup_lid_usage(inp, 'S10', 'BC', round(a_S10 * ra9, 0), 100.0)
            setup_lid_usage(inp, 'S10', 'GS', 0, 0.0)
        elif r9 == 2:
            setup_lid_usage(inp, 'S10', 'BC', 0, 0.0)
            setup_lid_usage(inp, 'S10', 'GS', round(a_S10 * ra9, 0), 100.0)
        elif r9 == 3:  # TRE is handled outside of SWMM
            setup_lid_usage(inp, 'S10', 'BC', 0, 0.0)
            setup_lid_usage(inp, 'S10', 'GS', 0, 0.0)
            t_total, t_imp = _trees_for_sub(a_S10, ra9, 'S10')
            trees_tot += t_total
            trees_imp += t_imp
        else:
            setup_lid_usage(inp, 'S10', 'BC', 0, 0.0)
            setup_lid_usage(inp, 'S10', 'GS', 0, 0.0)
        
        #### S11 ####
        r10 = int(x[14] * 4) + 1
        ra10 = x[15]
        
        if r10 == 1:
            setup_lid_usage(inp, 'S11', 'BC', round(a_S11 * ra10, 0), 100.0)
            setup_lid_usage(inp, 'S11', 'GS', 0, 0.0)
        elif r10 == 2:
            setup_lid_usage(inp, 'S11', 'BC', 0, 0.0)
            setup_lid_usage(inp, 'S11', 'GS', round(a_S11 * ra10, 0), 100.0)
        elif r10 == 3:  # TRE is handled outside of SWMM
            setup_lid_usage(inp, 'S11', 'BC', 0, 0.0)
            setup_lid_usage(inp, 'S11', 'GS', 0, 0.0)
            t_total, t_imp = _trees_for_sub(a_S11, ra10, 'S11')
            trees_tot += t_total
            trees_imp += t_imp
        else:
            setup_lid_usage(inp, 'S11', 'BC', 0, 0.0)
            setup_lid_usage(inp, 'S11', 'GS', 0, 0.0)

        # Run SWMM and compute average annual runoff
        avg_runoff_volume, results_df = calculate_annual_runoff_volume(inp)
    
        # Subtract 6 m³ per tree on impervious areas
        avg_runoff_volume = avg_runoff_volume - (trees_imp * 6.0)
    
        # Second objective: total BGF area (keep your existing implementation)
        total_bgf_area = calculate_total_bgf_area(x)
    
        # Terrain constraints (≤ 15% of respective subcatchment)
        constraints = []
        constraints.append((a_S5 * ra5 / a_S5) - 0.15 if r5 in [1, 2, 3] else 0.0)
        constraints.append((a_S7 * ra6 / a_S7) - 0.15 if r6 in [1, 2, 3] else 0.0)
        constraints.append((a_S8 * ra7 / a_S8) - 0.15 if r7 in [1, 2, 3] else 0.0)
        constraints.append((a_S9 * ra8 / a_S9) - 0.15 if r8 in [1, 2, 3] else 0.0)
        constraints.append((a_S10 * ra9 / a_S10) - 0.15 if r9 in [1, 2, 3] else 0.0)
        constraints.append((a_S11 * ra10 / a_S11) - 0.15 if r10 in [1, 2, 3] else 0.0)
    
        # Objectives (minimize runoff; maximize BGF via negative sign)
        out["F"] = [avg_runoff_volume, -total_bgf_area]
        out["G"] = constraints
    
        # Optional: expose tree counts for reporting
        out["trees_total"] = trees_tot
        out["trees_impervious"] = trees_imp
        
############################################################
########  5. HYPERARAMETERS FOR NSGA-II ###################
############################################################

problem = MyProblem()

algorithm = NSGA2(
    pop_size=population,
    eliminate_duplicates=True
)

res = minimize(problem,
               algorithm,
               ('n_gen',generation),
               seed=1,
               save_history=True,
               verbose=True)

############################################################
########  6. POST-PROCESSING AND RESULTS #######
############################################################
# 1) Objectives to DataFrame
#    F = [avg_runoff_volume, -total_bgf_area]
#    Make BGF area positive for reporting:
resF = res.F.copy()
resF[:, 1] = -resF[:, 1]  # flip sign back for reporting
resF_df = pd.DataFrame(resF, columns=['Runoff [m³]', 'BGF area [m²]'])

# 2) Decision variables to DataFrame
#    There are 16 decision variables in the same order you defined:
#    [S1_type, S2_type, S3_type, S4_type,
#     S5_type, S5_area,
#     S7_type, S7_area,
#     S8_type, S8_area,
#     S9_type, S9_area,
#     S10_type, S10_area,
#     S11_type, S11_area]
resX_df = pd.DataFrame(res.X, columns=[
    'x0','x1','x2','x3',
    'x4','x5',
    'x6','x7',
    'x8','x9',
    'x10','x11',
    'x12','x13',
    'x14','x15'
])

# 3) Maps from encoded int to readable labels
roof_map = {
    1: "GR5",
    2: "GR20",
    3: "None"
}
terrain_map = {
    1: "BC",    # bioretention cell
    2: "GS",    # grassed swale/area
    3: "TRE",   # trees
    4: "None"
}

# --- ROOFS: S1–S4 -------------------------------------------------------------

# S1
resX_df['x0'] = (resX_df['x0'] * 3).astype(int) + 1
resX_df['x0'] = resX_df['x0'].replace(roof_map)
resX_df = resX_df.rename(columns={'x0': 'S1 roof'})

# S2
resX_df['x1'] = (resX_df['x1'] * 3).astype(int) + 1
resX_df['x1'] = resX_df['x1'].replace(roof_map)
resX_df = resX_df.rename(columns={'x1': 'S2 roof'})

# S3
resX_df['x2'] = (resX_df['x2'] * 3).astype(int) + 1
resX_df['x2'] = resX_df['x2'].replace(roof_map)
resX_df = resX_df.rename(columns={'x2': 'S3 roof'})

# S4
resX_df['x3'] = (resX_df['x3'] * 3).astype(int) + 1
resX_df['x3'] = resX_df['x3'].replace(roof_map)
resX_df = resX_df.rename(columns={'x3': 'S4 roof'})


# --- TERRAIN: S5, S7, S8, S9, S10, S11 ----------------------------------------
# For BC/GS we report installed SWMM area = ratio * subcatchment area.
# For TRE/None we set installed SWMM area to 0 (trees handled outside SWMM).

# S5
resX_df['x4'] = (resX_df['x4'] * 4).astype(int) + 1
resX_df['x4'] = resX_df['x4'].replace(terrain_map)
resX_df = resX_df.rename(columns={'x4': 'S5 type'})

resX_df['S5 area [m²]'] = (resX_df['x5'] * a_S5).round(0)
resX_df.loc[~resX_df['S5 type'].isin(['BC', 'GS']), 'S5 area [m²]'] = 0
resX_df = resX_df.drop(columns=['x5'])

# S7
resX_df['x6'] = (resX_df['x6'] * 4).astype(int) + 1
resX_df['x6'] = resX_df['x6'].replace(terrain_map)
resX_df = resX_df.rename(columns={'x6': 'S7 type'})

resX_df['S7 area [m²]'] = (resX_df['x7'] * a_S7).round(0)
resX_df.loc[~resX_df['S7 type'].isin(['BC', 'GS']), 'S7 area [m²]'] = 0
resX_df = resX_df.drop(columns=['x7'])

# S8
resX_df['x8'] = (resX_df['x8'] * 4).astype(int) + 1
resX_df['x8'] = resX_df['x8'].replace(terrain_map)
resX_df = resX_df.rename(columns={'x8': 'S8 type'})

resX_df['S8 area [m²]'] = (resX_df['x9'] * a_S8).round(0)
resX_df.loc[~resX_df['S8 type'].isin(['BC', 'GS']), 'S8 area [m²]'] = 0
resX_df = resX_df.drop(columns=['x9'])

# S9
resX_df['x10'] = (resX_df['x10'] * 4).astype(int) + 1
resX_df['x10'] = resX_df['x10'].replace(terrain_map)
resX_df = resX_df.rename(columns={'x10': 'S9 type'})

resX_df['S9 area [m²]'] = (resX_df['x11'] * a_S9).round(0)
resX_df.loc[~resX_df['S9 type'].isin(['BC', 'GS']), 'S9 area [m²]'] = 0
resX_df = resX_df.drop(columns=['x11'])

# S10
resX_df['x12'] = (resX_df['x12'] * 4).astype(int) + 1
resX_df['x12'] = resX_df['x12'].replace(terrain_map)
resX_df = resX_df.rename(columns={'x12': 'S10 type'})

resX_df['S10 area [m²]'] = (resX_df['x13'] * a_S10).round(0)
resX_df.loc[~resX_df['S10 type'].isin(['BC', 'GS']), 'S10 area [m²]'] = 0
resX_df = resX_df.drop(columns=['x13'])

# S11
resX_df['x14'] = (resX_df['x14'] * 4).astype(int) + 1
resX_df['x14'] = resX_df['x14'].replace(terrain_map)
resX_df = resX_df.rename(columns={'x14': 'S11 type'})

resX_df['S11 area [m²]'] = (resX_df['x15'] * a_S11).round(0)
resX_df.loc[~resX_df['S11 type'].isin(['BC', 'GS']), 'S11 area [m²]'] = 0
resX_df = resX_df.drop(columns=['x15'])

# --- FINAL TABLE (objectives + decoded decisions) -----------------------------

final_df = pd.concat([resF_df, resX_df], axis=1)

# Save to Excel (same path you used earlier)
excel_path = r"C:\Users\ABI\OneDrive - NIVA\Documents\GitHub\SWMM_MOO\11_Optimization\11_Pareto_solutions.xlsx"
final_df.to_excel(excel_path, index=False)
print(f"Saved results to: {excel_path}")

# Quick plot
plt.figure()
plt.scatter(final_df['Runoff [m³]'], final_df['BGF area [m²]'])
plt.xlabel('Runoff [m³]')
plt.ylabel('BGF area [m²]')
plt.title('Pareto solutions: Runoff vs BGF area')
plt.tight_layout()
plt.show()