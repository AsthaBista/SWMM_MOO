import time
from pyswmm import Simulation, Nodes

# Start measuring real-world execution time
start_time = time.time()

# Simulation setup
with Simulation(r'C:\Users\ABI\OneDrive - NIVA\PhD_Work\Work\PartII\Loren\SWMM_MOO\SWMMFiles\Loren_singleblock.inp') as sim:
    # Simulation information
    print("Simulation info")
    flow_units = sim.flow_units
    print(f"Flow Units: {flow_units}")
    system_units = sim.system_units
    print(f"System Units: {system_units}")
    print(f"Start Time: {sim.start_time}")  # Use start_time
    print(f"End Time: {sim.end_time}")

    # Define Outfall Node
    OutfallNode = Nodes(sim)["O"]

    # Store simulation start time
    sim_start_time = sim.start_time  

    # Initialize variables
    peak_flow_outfall = 0.0
    time_of_peak_flow = None  # Store time of peak flow
    total_runoff_volume = 0.0  # Initialize accumulated runoff volume

    prev_time = sim_start_time  # Track previous time step

    # Run simulation with progress updates
    for step_count, step in enumerate(sim):
        current_time = sim.current_time  # Get the current simulation time

        # Compute time step duration (in seconds)
        step_duration = (current_time - prev_time).total_seconds()
        prev_time = current_time  # Update previous time step

        # Track outfall peak flow and time
        if OutfallNode.total_inflow > peak_flow_outfall:
            peak_flow_outfall = OutfallNode.total_inflow
            time_of_peak_flow = current_time  # Store the time of peak flow

        # ✅ Accumulate total runoff volume over time
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
    print(f"Time taken for Peak Flow: {time_taken_for_peak_hrs:.2f} hours")  # Print peak flow delay
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
