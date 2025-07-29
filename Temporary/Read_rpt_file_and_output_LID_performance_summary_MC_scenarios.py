import os
import pandas as pd
from swmm_api import read_rpt_file

# Paths
rpt_folder = r"C:\Users\ABI\My_Files\MonteCarlo\Results_WQ"
output_csv = r"C:\Users\ABI\My_Files\MonteCarlo\Results_WQ\lid_flows_summary.csv"

# Temporary storage for all simulation-year results
raw_lid_data = []

for file in os.listdir(rpt_folder):
    if file.endswith(".rpt") and file.startswith("rpt_sim"):
        path = os.path.join(rpt_folder, file)
        rpt = read_rpt_file(path)

        # Extract sim number and year
        sim_number = int(file.split('_')[1][3:])
        year = int(file.split('_')[2][4:].replace(".rpt", ""))

        rpt_lid = rpt.lid_performance_summary
        gr_drain, bc_outflow, bc_drain, gs_outflow = [], [], [], []

        if rpt_lid is not None:
            for i in range(1, 5):
                sub = f"S{i}"
                if sub in rpt_lid.index:
                    gr_drain.append(rpt_lid['Surface_Outflow_mm'].loc[sub])
            for i in [5, 7, 8, 9, 10, 11]:
                sub = f"S{i}"
                if sub in rpt_lid.index:
                    if rpt_lid['LID'].loc[sub] == 'BC':
                        bc_outflow.append(rpt_lid['Infil_Loss_mm'].loc[sub])
                        bc_drain.append(rpt_lid['Surface_Outflow_mm'].loc[sub])
                    else:
                        gs_outflow.append(rpt_lid['Infil_Loss_mm'].loc[sub])

        # Store raw yearly data
        raw_lid_data.append({
            'Sim': sim_number,
            'YEAR': year,
            'GR_DRAIN': sum(gr_drain),
            'BC_Outflow': sum(bc_outflow),
            'BC_Drain': sum(bc_drain),
            'GS_Outflow': sum(gs_outflow)
        })

# Convert to DataFrame
df_raw = pd.DataFrame(raw_lid_data)

# Group by Sim and take mean across years
df_summary = df_raw.groupby('Sim', as_index=False).mean(numeric_only=True)

# Round values
df_summary = df_summary.round(3)

# Save final summary
df_summary.to_csv(output_csv, index=False, sep=';')

print(f"Saved LID flow summary to:\n{output_csv}")
