import pandas as pd
import os

# Define the folder containing CSV files
folder_path = r'C:\Users\ABI\My_Files\MonteCarlo\Results'  

# List all CSV files in the folder and sort them
csv_files = sorted([f for f in os.listdir(folder_path) if f.endswith('.csv')])

# Create an empty list to store results
results = []

# Return periods to check
return_periods = [2, 5, 10, 20]

# Loop through each file
for idx, file in enumerate(csv_files, start=1):
    file_path = os.path.join(folder_path, file)

    # Read CSV (use ';' as separator)
    df = pd.read_csv(file_path, sep=';')

    # Compute total TR and PHI
    total_TR = df['TR'].mean()
    total_PRE = df['PRE'].sum()
    total_EVA = df['EVA'].sum()
    total_INF = df['INF'].sum()

    # Rank values and compute Weibull Distribution
    df['Rank'] = df['PR'].rank(ascending=False)
    df1 = df.sort_values(by='Rank', ascending=True)
    df1['Pe'] = df1['Rank'] / (len(df1) + 1)
    df1['T'] = 1 / df1['Pe']

    # Store results in a dictionary for the current file
    result_entry = {"sim_number": f"sim{idx}", "total_TR": round(total_TR, 2), "total_PRE": round(total_PRE, 2),
                    "total_EVA": round(total_EVA, 2), "total_INF": round(total_INF, 2)}

    for target_T in return_periods:
        df1["T_diff"] = (df1["T"] - target_T).abs()
        closest_row = df1.loc[df1["T_diff"].idxmin()]
        closest_PR = closest_row["PR"]
        result_entry[f"{target_T}yr"] = round(closest_PR, 3)

    # Append the result dictionary to the results list
    results.append(result_entry)

# Convert results to DataFrame
results_df = pd.DataFrame(results)

# Save results to CSV
output_file = r'C:\Users\ABI\OneDrive - NIVA\Documents\GitHub\SWMM_MOO\02_Water_Quantity\0202_Weibull_Frequency_analysis_results.csv'
results_df.to_csv(output_file, index=False, sep=';')

print(f"Results saved to {output_file}")
