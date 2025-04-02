import pandas as pd
from swmm_api.input_file import SwmmInput
from swmm_api.input_file.sections.lid import LIDUsage
from pyswmm import Simulation, Nodes, Subcatchments
import time
import datetime
from datetime import date, timedelta
import os


# Load CSV data
csv_file_path = r"C:\Users\ABI\My_Files\MonteCarlo\filtered_random_LID_data_with_trees.csv"
df = pd.read_csv(csv_file_path, delimiter=";")

# Load the SWMM input file
input_file = r"C:\Users\ABI\My_Files\MonteCarlo\SWMMFiles\Loren_singleblock_LT_temp_roofdisconnected.inp"
inp = SwmmInput(input_file)

# Create a DataFrame to store results
results = pd.DataFrame(
    columns=['YEAR','PR', 't_PR', 'TR'])
 # Extract the base filename without the directory
base_name = os.path.basename(input_file)  # e.g., "original_file.inp"
base_name_no_ext = base_name.replace(".inp", "")  # Remove .inp to modify

# Processing and simulation
# First each row of the csv file is iterated, and the LID areas from the file are entered into the model
# Secondly, in the same row loop, which is also a scenario loop, simulation is run

for sim_number in range(50,len(df)):  # Loop through indices in the csv file
    row_data = df.iloc[sim_number]  
    
    # Reload the SWMM input file to reset modifications
    inp = SwmmInput(input_file)
    
    
    modified_file = os.path.join(
    r"C:\Users\ABI\My_Files\MonteCarlo\SWMMFiles\Modified",
    f"{base_name_no_ext}_modified_row{sim_number + 1}.inp")
    
    # print(f"--- LID USAGE ENTRIES FOR SIMULATION {sim_number} ---")

 #   Assign LID for S1-S4 (columns 3-6). These are roof subcatchments
    for i, subcatchment in enumerate(["S1", "S2", "S3", "S4"], start=1):
        lid_area = row_data[f"S{i}"]
        lid_type = row_data["Type"]
        
        # Assigning green roofs for each of the four subcatchments
        if lid_area > 0:
            inp["LID_USAGE"][(subcatchment, lid_type)] = LIDUsage(
                subcatchment=subcatchment,
                lid=lid_type,
                n_replicate=1,
                area=lid_area,
                width=10, #not sure
                saturation_init=0.0,
                impervious_portion=100.0,
                route_to_pervious=0.0,
                fn_lid_report='*',
                drain_to='*',
                from_pervious=0.0
            )
           # print(f"{subcatchment}, {lid_type}, {lid_area}")
    
    # Assign LID for S5, S7-S11 (skipping S6) - terrain subcatchments
    for i in [5, 7, 8, 9, 10, 11]:  # S5, S7-S11
        lid_area = row_data[f"S{i}"]
        lid_type = row_data[f"S{i}_Type"]
        new_area = row_data[f"S{i}_Aimp"]
        
        inp.SUBCATCHMENTS[f"S{i}"].area = round(new_area * 0.0001,4) # New impervious area or here total subcatchment area (changes only if there is a tree)
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




    # Defining the time to simulate

    yr_start =  1968
    yr_stop =   2023
    
    for year in range(yr_start, yr_stop + 1):
        sim_start = datetime.date(year, 5, 1)  # Definerer start-dato for simulering (årstall, måned, dag)
        sim_stopp = datetime.date(year, 10, 31)  # Definerer slutt-dato for simulering (årstall, måned, dag)

        # Setter perioder for kalibrering
        inp.OPTIONS['START_DATE'] = sim_start
        inp.OPTIONS['END_DATE'] = sim_stopp
        inp.OPTIONS['REPORT_START_DATE'] = inp.OPTIONS['START_DATE']
        temp_file = r"C:\Users\ABI\My_Files\MonteCarlo\SWMMFiles\model_temp.inp"
        inp.write_file(temp_file)
        

        # Initialize peak flow time to None before the loop
        time_of_peak_flow = None  
        # Simulation for the temporary file with the defined time
        start_time = time.time() # start of simulation
        

        with Simulation(temp_file) as sim:
            # print("Simulation Info")
            # print(f"Flow Units: {sim.flow_units}")
            # print(f"Start Time: {sim.start_time}")
            # print(f"End Time: {sim.end_time}")
            print("done")
            OutfallNode = Nodes(sim)["O"]
            peak_flow_outfall = 0.0
            total_runoff_volume = 0.0
            prev_time = sim.start_time
            
            for step_count, step in enumerate(sim):
                
                # Getting the current time, previous time and step duration
                current_time = sim.current_time
                step_duration = (current_time - prev_time).total_seconds()
                prev_time = current_time
                
                # Getting peak runoff and time of peak
                if OutfallNode.total_inflow > peak_flow_outfall: 
                    peak_flow_outfall = OutfallNode.total_inflow
                    time_of_peak_flow = current_time
                    
                # Getting total runoff
                total_runoff_volume += OutfallNode.total_inflow * step_duration # cumulative runoff throughout the duration of the step 
    
                if step_count % 100 == 0:
                    print(f"Simulation {sim_number}, Year {year}: {round(sim.percent_complete * 100)}% completed")
    
        # print("Simulation completed!")
        # print(f"Peak Flow: {peak_flow_outfall:.3f} m³/s")
        # print(f"Total Runoff Volume: {total_runoff_volume:.3f} m³")
    # 
        
       
        
        # Store results in structured DataFrame format
        results.loc[year - yr_start + 1, 'YEAR'] =   year
        results.loc[year - yr_start + 1, 'PR'] =   peak_flow_outfall
        results.loc[year - yr_start + 1, 't_PR'] =   time_of_peak_flow
        results.loc[year - yr_start + 1, 'TR'] =   total_runoff_volume
        
        
        
    # Convert results dictionary to DataFrame and save with ';' delimiter
    results_df = pd.DataFrame(results)
    results_df.to_csv(rf"C:\Users\ABI\My_Files\MonteCarlo\Results\swmm_MC_results{sim_number}.csv", index=False, sep=';')
  
    
end_time = time.time()
elapsed_time = (end_time - start_time)/60
print(f"Total simulation time for Simulation {sim_number}: {elapsed_time:.2f} minutes.")