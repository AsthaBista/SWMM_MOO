# -*- coding: utf-8 -*-
"""
Created on Wed Jun  4 12:01:14 2025

@author: ABI
"""

# -*- coding: utf-8 -*-
"""
Created on Wed Jun  4 11:08:14 2025
Modified: Base Runoff Simulation (No Tree)
@author: ABI
"""

import pandas as pd
import numpy as np

# Load dataset
df = pd.read_csv(r"C:\Users\ABI\OneDrive - NIVA\PhD_Work\Work\PartII\Loren\Climate_cleaned_data.csv", delimiter=';')
df.rename(columns={
    'Date': 'date',
    'Rain(mm)': 'rainfall_mm',
    'Max': 'Tmax',
    'Min': 'Tmin'
}, inplace=True)
df['date'] = pd.to_datetime(df['date'], dayfirst=True)
df['Tavg'] = (df['Tmax'] + df['Tmin']) / 2

# Hargreaves method for PE
hargreaves_factor = 0.0023 * 15  # Adjusted for Ra scaling
df['PE_mm'] = hargreaves_factor * (df['Tavg'] + 17.8) * np.sqrt(df['Tmax'] - df['Tmin'])
df['PE_m'] = df['PE_mm'] / 1000

# Constants for ground model
CANOPY_AREA = 10     # m² (still used for converting mm to liters)
Simax = 0.0015       # Max ground depression storage [m]
Svi = 0.0            # Initial ground depression storage

# Results list
results_base = []

# Time-step simulation
for _, row in df.iterrows():
    Pt = row['rainfall_mm'] / 1000  # Rain in meters
    PE = row['PE_m']                # Evap in meters

    # Ground evaporation and runoff
    Evi = (Svi / Simax) * PE if Simax > 0 else 0
    Evi = min(Evi, Svi)
    Rv = max(Pt - (Simax - Svi) - Evi, 0)
    Svi = min(Svi + Pt - Evi, Simax)

    results_base.append({
        "date": row['date'],
        "rain_mm": row['rainfall_mm'],
        "PE_mm": row['PE_mm'],
        "ground_evap_mm": Evi * 1000,
        "surface_runoff_mm": Rv * 1000
    })

# Create DataFrame
runoff_df = pd.DataFrame(results_base)

# Extract month and year
runoff_df['month'] = runoff_df['date'].dt.month
runoff_df['year'] = runoff_df['date'].dt.year

# Filter for May to October
seasonal_df = runoff_df[(runoff_df['month'] >= 5) & (runoff_df['month'] <= 10)]

# Group by year
annual_runoff = seasonal_df.drop(columns=['date', 'month']).groupby('year').sum()

# Save to CSV
annual_runoff.to_csv(r"C:\Users\ABI\OneDrive - NIVA\PhD_Work\Work\PartII\Loren\base_runoff_calculations.csv", sep=';')

# Optional: print first 50 years
print(annual_runoff.head(50))
