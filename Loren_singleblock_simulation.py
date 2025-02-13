import time
from pyswmm import Simulation, Nodes

# Start measuring time
start_time = time.time()

# Simulation setup
with Simulation(r'C:\Users\ABI\OneDrive - NIVA\PhD_Work\Work\PartII\Loren\SWMMFiles\Loren_singleblock.inp') as sim:
    # Simulation information
    print("Simulation info")
    flow_units = sim.flow_units
    print(f"Flow Units: {flow_units}")
    system_units = sim.system_units
    print(f"System Units: {system_units}")
    print(f"Start Time: {sim.start_time}")
    print(f"End Time: {sim.end_time}")

    # Define Outfall Node
    OutfallNode = Nodes(sim)["O"] 

    # Initialize variables
    peak_flow_outfall = 0.0
    total_runoff_volume = 0.0

    # Run simulation with progress updates
    for step_count, step in enumerate(sim):
        # Track outfall peak flow
        if OutfallNode.total_inflow > peak_flow_outfall:
            peak_flow_outfall = OutfallNode.total_inflow

        # Update total runoff volume
        total_runoff_volume = OutfallNode.total_inflow

        # Print progress every 10% or 100 steps
        if step_count % 100 == 0:
            print(f"Simulation running... {round(sim.percent_complete * 100)}% completed")

    print("Simulation completed!")

# Convert results to appropriate units
peak_flow_m3s = peak_flow_outfall  # Already in m³/s from PySWMM
total_runoff_volume_m3 = total_runoff_volume  # Already in m³ from PySWMM

# Output results
print(f"Peak Flow at Outfall: {peak_flow_m3s:.3f} m³/s")
print(f"Total Runoff Volume at Outfall: {total_runoff_volume_m3:.2f} m³")

# Measure and format elapsed time
end_time = time.time()
elapsed_time = end_time - start_time
hours, remainder = divmod(elapsed_time, 3600)
minutes, seconds = divmod(remainder, 60)
print(f"Elapsed time: {int(hours)} hrs, {int(minutes)} mins, {seconds:.2f} secs")
