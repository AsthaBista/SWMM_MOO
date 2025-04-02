import time
from pyswmm import Simulation, Nodes

# Start measuring real-world execution time
start_time = time.time()

# Define input, custom report, and output files
input_file = r'C:\Users\ABI\OneDrive - NIVA\PhD_Work\Work\PartII\Loren\SWMM_MOO\SWMMFiles\Loren_singleblock_LT_temp_roofdisconnected_modified.inp'
# custom_rpt_file = r'C:\Users\ABI\OneDrive - NIVA\PhD_Work\Work\PartII\Loren\SWMM_MOO\SWMMFiles\OutFiles\LT_p20sw.rpt'
# custom_out_file = r'C:\Users\ABI\OneDrive - NIVA\PhD_Work\Work\PartII\Loren\SWMM_MOO\SWMMFiles\OutFiles\LT_p20sw.out'

# Simulation setup with custom report file
with Simulation(input_file) as sim:
    print("Simulation info")
    print(f"Flow Units: {sim.flow_units}")
    print(f"System Units: {sim.system_units}")
    print(f"Start Time: {sim.start_time}")
    print(f"End Time: {sim.end_time}")

    # Define Outfall Node
    OutfallNode = Nodes(sim)["O"]

    # Store simulation start time
    sim_start_time = sim.start_time  

    # Initialize variables
    peak_flow_outfall = 0.0
    time_of_peak_flow = None
    total_runoff_volume = 0.0

    prev_time = sim_start_time  # Track previous time step

    # Run simulation with progress updates
    for step_count, step in enumerate(sim):
        current_time = sim.current_time  # Get the current simulation time
        step_duration = (current_time - prev_time).total_seconds()
        prev_time = current_time  # Update previous time step

        # Track outfall peak flow and time
        if OutfallNode.total_inflow > peak_flow_outfall:
            peak_flow_outfall = OutfallNode.total_inflow
            time_of_peak_flow = current_time

        #Accumulate total runoff volume over time
        total_runoff_volume += OutfallNode.total_inflow * step_duration

        # Print progress every 100 steps
        if step_count % 100 == 0:
            print(f"Simulation running... {round(sim.percent_complete * 100)}% completed")

    print("Simulation completed!")

# Convert results to appropriate units
peak_flow_m3s = peak_flow_outfall  # Already in m³/s from PySWMM
total_runoff_volume_m3 = total_runoff_volume  # Corrected to accumulate over time

# Compute time taken for peak flow in hours **only if peak flow occurred**
if time_of_peak_flow:
    time_taken_for_peak_hrs = (time_of_peak_flow - sim_start_time).total_seconds() / 3600
    print(f"Time taken for Peak Flow: {time_taken_for_peak_hrs:.2f} hours")
else:
    print("Warning: No peak flow detected!")

# Output results
print(f"Peak Flow at Outfall: {peak_flow_m3s:.3f} m³/s")
print(f"Total Runoff Volume at Outfall: {total_runoff_volume_m3:.3f} m³")

# Measure and format elapsed time
end_time = time.time()
elapsed_time = end_time - start_time
hours, remainder = divmod(elapsed_time, 3600)
minutes, seconds = divmod(remainder, 60)
print(f"Elapsed time: {int(hours)} hrs, {int(minutes)} mins, {seconds:.2f} secs")

# Print confirmation that report file was saved
# print(f"Custom SWMM report file saved as: {custom_rpt_file}")
