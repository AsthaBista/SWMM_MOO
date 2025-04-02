import pandas as pd
from swmm_api.input_file import SwmmInput
from swmm_api.input_file.sections.lid import LIDUsage
from pyswmm import Simulation, Nodes, Subcatchments
import time

# Load CSV data
csv_file_path = r"C:\Users\ABI\OneDrive - NIVA\PhD_Work\Work\PartII\Loren\filtered_random_LID_data.csv"
df = pd.read_csv(csv_file_path, delimiter=";")

# Load the SWMM input file
input_file = r"C:\Users\ABI\OneDrive - NIVA\PhD_Work\Work\PartII\Loren\SWMM_MOO\SWMMFiles\Loren_singleblock_LT_temp_roofdisconnected.inp"
inp = SwmmInput(input_file)

# Create a DataFrame to store results
results = {
    "Simulation #": [],
    "Peak Flow (m³/s)": [],
    "Total Runoff Volume (m³)": [],
    "Simulation Time (s)": []
}

# Process first two rows only
for sim_number, row in enumerate(df.iloc[:3].iterrows(), start=1):
    _, row_data = row
    modified_file = input_file.replace(".inp", f"_modified_row{sim_number}.inp")
    
    # Ensure LID_USAGE section exists and reset it for each row
    inp["LID_USAGE"] = LIDUsage.create_section()

    print(f"--- LID USAGE ENTRIES FOR SIMULATION {sim_number} ---")

    # Assign LID for S1-S4 (columns 3-6)
    for i, subcatchment in enumerate(["S1", "S2", "S3", "S4"], start=1):
        lid_area = row_data[f"S{i}"]
        lid_type = row_data["Type"]
        
        if lid_area > 0:
            inp["LID_USAGE"][(subcatchment, lid_type)] = LIDUsage(
                subcatchment=subcatchment,
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
            print(f"{subcatchment}, {lid_type}, {lid_area}")
    
    # Assign LID for S5, S7-S11 (skipping S6)
    for i in [5, 7, 8, 9, 10, 11]:  # S5, S7-S11
        lid_area = row_data[f"S{i}"]
        lid_type = row_data[f"S{i}_Type"]
        
        if lid_area > 0:
            inp["LID_USAGE"][(f"S{i}", lid_type)] = LIDUsage(
                subcatchment=f"S{i}",
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
            print(f"S{i}, {lid_type}, {lid_area}")

    # Save modified SWMM input file
    inp.write_file(modified_file)
    print(f"LID Usage updated. Saved as: {modified_file}")

    # Run the SWMM simulation
    start_time = time.time()
    with Simulation(modified_file) as sim:
        print("Simulation Info")
        print(f"Flow Units: {sim.flow_units}")
        print(f"Start Time: {sim.start_time}")
        print(f"End Time: {sim.end_time}")
        
        OutfallNode = Nodes(sim)["O"]
        peak_flow_outfall = 0.0
        total_runoff_volume = 0.0
        prev_time = sim.start_time

        for step_count, step in enumerate(sim):
            current_time = sim.current_time
            step_duration = (current_time - prev_time).total_seconds()
            prev_time = current_time

            if OutfallNode.total_inflow > peak_flow_outfall:
                peak_flow_outfall = OutfallNode.total_inflow
                time_of_peak_flow = current_time

            total_runoff_volume += OutfallNode.total_inflow * step_duration

            if step_count % 100 == 0:
                print(f"Simulation {sim_number}: {round(sim.percent_complete * 100)}% completed")

    print("Simulation completed!")
    print(f"Peak Flow: {peak_flow_outfall:.3f} m³/s")
    print(f"Total Runoff Volume: {total_runoff_volume:.3f} m³")

    end_time = time.time()
    elapsed_time = end_time - start_time
    hours, minutes = divmod(elapsed_time // 60, 60)
    seconds = elapsed_time % 60
    print(f"Elapsed time: {int(hours)} hrs, {int(minutes)} mins, {seconds:.2f} secs")
    
    # Store results in structured DataFrame format
    results["Simulation #"].append(sim_number)
    results["Peak Flow (m³/s)"].append(peak_flow_outfall)
    results["Total Runoff Volume (m³)"].append(total_runoff_volume)
    results["Simulation Time (s)"].append(elapsed_time)

# Convert results dictionary to DataFrame and save with ';' delimiter
results_df = pd.DataFrame(results)
results_df.to_csv("swmm_simulation_results.csv", index=False, sep=';')
print("Results saved to swmm_simulation_results.csv")
