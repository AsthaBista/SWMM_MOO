# -*- coding: utf-8 -*-
"""
# This script conducts a sensitivity analysis by varying imperviousness, width, and depression storage.
"""

import re
import time
from pyswmm import Simulation

# Define base input file
base_inp = r'C:\Users\ABI\OneDrive - NIVA\PhD_Work\Work\PartII\Loren\SWMMFiles\Loren_singleblock.inp'
rpt_file = base_inp.replace(".inp", ".rpt")

# Define sensitivity ranges
imperviousness_values = [30, 40, 50, 60, 70]  # Percentage
width_values = [10, 15, 20, 25, 30]  # Example width values (adjust based on your model)
depression_storage_values = [1, 3, 5, 7, 9]  # Depression storage in mm

def modify_inp_file(inp_path, parameter, new_value):
    """
    Modify a given parameter (imperviousness, width, depression storage) in a SWMM INP file.

    Parameters:
    - inp_path: str -> Path to the SWMM .inp file
    - parameter: str -> The parameter to modify ("imperviousness", "width", "depression_storage")
    - new_value: float/int -> The new value to set for the parameter
    """
    with open(inp_path, 'r') as file:
        lines = file.readlines()

    # Define the column positions for different parameters
    param_indices = {
        "imperviousness": 4,  # 5th column
        "width": 3,           # 4th column
        "depression_storage": 5  # 6th column
    }

    if parameter not in param_indices:
        raise ValueError(f"Invalid parameter: {parameter}. Choose from {list(param_indices.keys())}")

    modified_lines = []
    for line in lines:
        if line.startswith("Subcatchment"):  # Find subcatchment data
            parts = line.split()
            if len(parts) > param_indices[parameter]:  # Ensure the parameter exists
                parts[param_indices[parameter]] = str(new_value)  # Modify the selected parameter
            line = " ".join(parts) + "\n"  # Reconstruct the modified line
        modified_lines.append(line)

    # Write the modified file back
    with open(inp_path, 'w') as file:
        file.writelines(modified_lines)

    print(f"Updated {parameter} in {inp_path} to {new_value}")

# Store results
sensitivity_results = []

# Run simulations with different values for imperviousness, width, and depression storage
for imp, width, dep_storage in zip(imperviousness_values, width_values, depression_storage_values):
    print(f"\nRunning simulation with Imperviousness = {imp}%, Width = {width}, Depression Storage = {dep_storage} mm")

    # Modify each parameter in the INP file
    modify_inp_file(base_inp, "imperviousness", imp)
    modify_inp_file(base_inp, "width", width)
    modify_inp_file(base_inp, "depression_storage", dep_storage)

    # Start simulation
    start_time = time.time()
    with Simulation(base_inp) as sim:
        sim.execute()  # Run SWMM simulation

    # Extract total runoff volume from RPT file
    total_runoff = None
    with open(rpt_file, 'r') as file:
        for line in file:
            if "TOTAL RUNOFF VOLUME" in line.upper():
                match = re.search(r'([\d.]+)', line)
                if match:
                    total_runoff = float(match.group(1))
                    break

    elapsed_time = time.time() - start_time
    sensitivity_results.append((imp, width, dep_storage, total_runoff, elapsed_time))
    print(f"Total Runoff: {total_runoff:.2f} m³, Time: {elapsed_time:.2f} sec")

# Compute percentage changes compared to baseline (assumed at index 2)
baseline_runoff = sensitivity_results[2][3]  # Reference (50% imperviousness, 20 width, 5 dep. storage)

# Print summary with percentage changes
print("\nSensitivity Analysis Results:")
print("Imperviousness (%) | Width | Dep. Storage | Total Runoff (m³) | % Change | Time (s)")
print("-" * 80)

for result in sensitivity_results:
    imp, width, dep_storage, runoff, time_taken = result
    percent_change = ((runoff - baseline_runoff) / baseline_runoff) * 100 if baseline_runoff else 0
    print(f"{imp:15} | {width:5} | {dep_storage:12} | {runoff:17.2f} | {percent_change:8.2f}% | {time_taken:.2f} sec")
