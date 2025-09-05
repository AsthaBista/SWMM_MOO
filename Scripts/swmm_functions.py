# Function to calculate annual runoff volume from SWMM simulation
import os
import datetime
import tempfile
import numpy as np
import pandas as pd
from swmm_api import read_rpt_file
from pyswmm import Simulation, Nodes

def calculate_annual_runoff_volume(inp, yr_start=2010, yr_stop=2020):
    """
    Calculate annual total runoff volume from SWMM simulation
    
    Parameters:
    inp: SWMM input object
    yr_start: start year for simulation
    yr_stop: end year for simulation
    
    Returns:
    avg_total_volume: average annual total runoff volume
    results_df: DataFrame with detailed results for each year
    """
    
    # Create temporary files for simulation
    with tempfile.NamedTemporaryFile(suffix='.inp', delete=False) as temp_inp_file:
        temp_inp = temp_inp_file.name
    temp_rpt = temp_inp.replace('.inp', '.rpt')
    
    results = []
    
    # Loop through each year in simulation period
    for year in range(yr_start, yr_stop + 1):
        # Set simulation period for each year (May 1 to Oct 31)
        sim_start = datetime.date(year, 5, 1)
        sim_end = datetime.date(year, 10, 31)
        
        # Update input options with simulation dates
        inp.OPTIONS['START_DATE'] = sim_start
        inp.OPTIONS['END_DATE'] = sim_end
        inp.OPTIONS['REPORT_START_DATE'] = sim_start
        
        # Write temporary input file
        inp.write_file(temp_inp)

        print(f"Simulating year {year}...")

        inflows = []
        timestamps = []

        # Run SWMM simulation
        with Simulation(temp_inp) as sim:
            node = Nodes(sim)["O"]  # Outlet node
            for step in sim:
                inflows.append(node.total_inflow)
                timestamps.append(sim.current_time)

        # Calculate flow metrics from simulation results
        sim_q = np.array(inflows)
        peak_flow = round(sim_q.max(), 3)
        peak_index = sim_q.argmax()
        peak_time = timestamps[peak_index]
        total_volume = round(sim_q.sum() * 60, 3)  # Convert to volume (assuming 1-min steps)
        
        # Read report file for additional hydrological metrics
        try:
            rpt = read_rpt_file(temp_rpt)
            PRE = rpt.runoff_quantity_continuity['Total Precipitation']['Depth_mm']
            EVA = rpt.runoff_quantity_continuity['Evaporation Loss']['Depth_mm']
            INF = rpt.runoff_quantity_continuity['Infiltration Loss']['Depth_mm']
            PHI = round((PRE - EVA - INF) / PRE, 2) if PRE > 0 else 0
        except:
            # Set default values if report file reading fails
            PRE = 0
            EVA = 0
            INF = 0
            PHI = 0

        # Store results for this year
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

    # Create DataFrame from results
    results_df = pd.DataFrame(results)
    
    # Calculate average annual total runoff volume
    avg_total_volume = results_df['TR'].mean()
    
    # Clean up temporary files
    try:
        os.remove(temp_inp)
        os.remove(temp_rpt)
    except:
        pass
    
    return avg_total_volume


######################################################
#######      3. HELPER FUNCTIONS                ######
######################################################

from swmm_api import LIDUsage

def setup_lid_usage(inp, subcatchment, lid_type, area, impervious_portion=100.0):
    """
    Setup LID usage for a subcatchment with proper initialization
    """
    # Remove any existing LID usage for this subcatchment and lid type
    if (subcatchment, lid_type) in inp.LID_USAGE:
        del inp.LID_USAGE[(subcatchment, lid_type)]
    
    # Create new LID usage with proper parameters
    inp.LID_USAGE[(subcatchment, lid_type)] = LIDUsage(
        subcatchment=subcatchment,
        lid=lid_type,
        n_replicate=1,
        area=area,
        width=10,
        saturation_init=0.0,
        impervious_portion=impervious_portion,
        route_to_pervious=0.0,
        fn_lid_report='*',
        drain_to='*',
        from_pervious=0.0
    )