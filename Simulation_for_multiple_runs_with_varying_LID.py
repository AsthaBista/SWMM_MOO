"""
# This script conducts a sensitivity analysis by varying imperviousness, width, and depression storage.
"""

import time
from pyswmm import Simulation, Subcatchments, LidControls

# Start measuring real-world execution time
start_time = time.time()

# Define input, custom report, and output files
input_file = r'C:\Users\ABI\OneDrive - NIVA\PhD_Work\Work\PartII\Loren\SWMM_MOO\SWMMFiles\Loren_singleblock_LT_roofdisconnected.inp'

# # Define subcatchment and LID control names
# subcatchment_name = "S1"  # Replace with actual subcatchment name
# lid_name = "GR5"  # Replace with actual LID control name


# # Define LID area as a variable (change this as needed)
# lid_area = 100  # Example: 35% of the subcatchment


with Simulation(input_file) as sim:
    for lid_control in LidControls(sim):
        print(lid_control)























# # Function to modify the SWMM input file and update LID area
# def set_lid_usage(inp_file, subcatchment, lid_name, area):
#     with open(inp_file, "r") as file:
#         lines = file.readlines()

#     lid_usage_section = False
#     new_lines = []
#     updated = False

#     for line in lines:
#         # Detect when LID_USAGE section starts
#         if "[LID_USAGE]" in line:
#             lid_usage_section = True
#             new_lines.append(line)
#             continue

#         # If inside LID_USAGE section, check if entry exists
#         if lid_usage_section and subcatchment in line and lid_name in line:
#             parts = line.split()
#             if len(parts) >= 5:  # Ensure we have enough elements
#                 parts[3] = str(area)  # Update the LID area percentage
#                 updated_line = "  ".join(parts) + "\n"
#                 new_lines.append(updated_line)
#                 updated = True
#                 continue

#         new_lines.append(line)

#     # If LID entry was not found, add it
#     if not updated:
#         new_lines.append(f"{subcatchment} {lid_name} 1 {area} 100 0 0 0 0 * *\n")

#     # Write back the modified file
#     with open(inp_file, "w") as file:
#         file.writelines(new_lines)

# # Assign the LID control with the specified area
# set_lid_usage(input_file, subcatchment_name, lid_name, lid_area)

# # Run the simulation
# with Simulation(input_file) as sim:
#     print("Simulation info")
#     print(f"Flow Units: {sim.flow_units}")
#     print(f"System Units: {sim.system_units}")
#     print(f"Start Time: {sim.start_time}")
#     print(f"End Time: {sim.end_time}")

#     # Access subcatchment
#     sc = Subcatchments(sim)[subcatchment_name]
#     print(f"Subcatchment {subcatchment_name} is included in the simulation.")

#     # Verify LID controls
#     lid_controls = LidControls(sim)
#     if lid_name in lid_controls:
#         print(f"LID Control '{lid_name}' is correctly recognized in the simulation with area {lid_area}%.")
#     else:
#         print(f"Error: LID Control '{lid_name}' not found.")