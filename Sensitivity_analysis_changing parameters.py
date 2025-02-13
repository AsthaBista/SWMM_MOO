# -*- coding: utf-8 -*-
"""
# In this script, a sensitivity analysis is conducted using a range of values for various 
# determining parameters
"""

import re
import time
from pyswmm import Simulation

# Define base input file
base_inp = r'C:\Users\ABI\OneDrive - NIVA\PhD_Work\Work\PartII\Loren\SWMMFiles\Loren_singleblock.inp'
rpt_file = base_inp.replace(".inp", ".rpt")

# Define sensitivity ranges
imperviousness_values = [30, 40, 50, 60, 70]  # Different sensitivity levels

# Function to modify imperviousness in the INP file
def modify_inp_file(inp_path, new_value):
    with open(inp_path, 'r') as file:
        lines = file.readlines()

    modified_lines = []
    for line in lines:
        if line.startswith("Subcatchment"):  # Locate the subcatchment section
            parts = line.split()
            if len(parts) > 4:
                parts[4] = str(new_value)  # Modify imperviousness value
            line = " ".join(parts) + "\n"
        modified_lines.append(line)

    with open(inp_path, 'w') as file:
        file.writelines(modified_lines)

# Store results
sensitivity_results = []

# Run simulations with different imperviousness values
for value in imperviousness_values:
    print(f"Running simulation with Imperviousness = {value}%")
    modify_inp_file(base_inp, value)

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
    sensitivity_results.append((value, total_runoff, elapsed_time))
    print(f"Total Runoff: {total_runoff:.2f} m³, Time: {elapsed_time:.2f} sec")

# Print summary
print("\nSensitivity Analysis Results:")
for result in sensitivity_results:
    print(f"Imperviousness: {result[0]}%, Total Runoff: {result[1]:.2f} m³, Time: {result[2]:.2f} sec")
