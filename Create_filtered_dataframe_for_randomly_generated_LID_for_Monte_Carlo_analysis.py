
"""
This script is the first step in the Monte Carlo Analysis
Random percentages of LID area for each subcatchments are prepared in an excel file
The excel file consists of many columns that are not necessary
This script prepares a cleaned up dataframe of the random LID percentages
It prepares an output called filtered_random_LID_data.csv.

"""
import pandas as pd

csv_file = pd.read_csv(r'C:\Users\ABI\OneDrive - NIVA\PhD_Work\Work\PartII\Loren\Random_generated_LID_sqm.csv',sep=';')
#print(csv_file.head())

df = pd.DataFrame(csv_file)
#print(df.head())

# Create an empty dictionary
lid_values = {}

# Define index positions to iterate over
i_values = [10, 14, 18, 22, 26, 30]  # Column indices for Terrain Type (BC, GS, TRE)
j_values = [5, 7, 8, 9, 10, 11]   # Terrain subcatchment numbers

# Loop through the first 5 rows
for index, row in df.iterrows():
    sim = row.iloc[0]  # Use "Sim" as the key

    # Apply conditional logic based on the Type column
    if row.iloc[1] == "5cm":
        base_values = {
            "Type": "GR5",  # New column indicating GR5
            "S1": row.iloc[2],
            "S2": row.iloc[3],
            "S3": row.iloc[4],
            "S4": row.iloc[5],
        }
    else:
        base_values = {
            "Type": "GR20",  # New column indicating GR20
            "S1": row.iloc[6],
            "S2": row.iloc[7],
            "S3": row.iloc[8],
            "S4": row.iloc[9],
        }

    # Dictionary to store terrain type values
    row_values = {}

    # Loop through specified i-values (Type: BC, GS, TRE)
    for i, j in zip(i_values, j_values):
        row_values[f"S{j}_Type"] = row.iloc[i]
        
        if row.iloc[i] == "BC":
            row_values[f"S{j}"] = row.iloc[i + 1]
        
        elif row.iloc[i] == "GS":
            row_values[f"S{j}"] = row.iloc[i + 2]
        elif row.iloc[i] == "TRE":
            row_values[f"S{j}"] = row.iloc[i + 3]

    # Merge the base LID values and terrain type values
    lid_values[sim] = {**base_values, **row_values}  # Merging both dictionaries

# Convert dictionary to DataFrame for better readability
filtered_df = pd.DataFrame.from_dict(lid_values, orient="index")

# Print or save the filtered DataFrame
print(filtered_df)

filtered_df.to_csv(r"C:\Users\ABI\OneDrive - NIVA\PhD_Work\Work\PartII\Loren\filtered_random_LID_data.csv", index=True, sep=";")