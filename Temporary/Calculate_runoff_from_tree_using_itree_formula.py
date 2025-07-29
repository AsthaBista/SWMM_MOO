# -*- coding: utf-8 -*-
"""
Created on Wed Jun  4 11:08:14 2025

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

# Constants for canopy and ground model
CANOPY_AREA = 10     # m²
SL = 0.0002          # m
LAI = 5              # Leaf Area Index (adjust for species)
k = 0.7              # Extinction coefficient
Svmax = SL * LAI     # Max canopy storage [m]
Simax = 0.0015       # Max ground depression storage [m]

# Initialize storages
Sv = 0.0   # canopy storage
Svi = 0.0  # ground depression storage

# Canopy cover fraction
c = 1 - np.exp(-k * LAI)

# Simulation results
results = []

# Time-step simulation
for _, row in df.iterrows():
    Pt = row['rainfall_mm'] / 1000  # Rain in meters
    PE = row['PE_m']                # Evap in meters

    # Rainfall partition
    Ptt = Pt * (1 - c)  # Through canopy
    Pct = Pt - Ptt      # Intercepted

    # Canopy evaporation
    Ev = ((Sv / Svmax) ** (2/3)) * PE if Svmax > 0 else 0
    Ev = min(Ev, Sv)
    Sv = min(Sv + Pct - Ev, Svmax)

    # Drip if saturated
    Dt = max(Pct - (Svmax - Sv) - Ev, 0) if Sv == Svmax else 0

    # Ground evap and runoff
    Evi = (Svi / Simax) * PE if Simax > 0 else 0
    Evi = min(Evi, Svi)
    Rv = max(Ptt + Dt - (Simax - Svi) - Evi, 0)
    Svi = min(Svi + Ptt + Dt - Evi, Simax)

    results.append({
        "date": row['date'],
        "rain_mm": row['rainfall_mm'],
        "PE_mm": row['PE_mm'],
        "canopy_evap_mm": Ev * 1000,
        "canopy_storage_mm": Sv * 1000,
        "canopy_drip_mm": Dt * 1000,
        "ground_evap_mm": Evi * 1000,
        "surface_runoff_mm": Rv * 1000
    })

# Results DataFrame
runoff_df = pd.DataFrame(results)

runoff_df['month'] = runoff_df['date'].dt.month
runoff_df['year'] = runoff_df['date'].dt.year

# Filter for months May (5) through October (10)
seasonal_df = runoff_df[(runoff_df['month'] >= 5) & (runoff_df['month'] <= 10)]

# Group by year and sum only selected months
annual_runoff = seasonal_df.drop(columns=['date', 'month']).groupby('year').sum()

print(annual_runoff.head(50))
annual_runoff.to_csv(r"C:\Users\ABI\OneDrive - NIVA\PhD_Work\Work\PartII\Loren\tree_model_calculations.csv", sep=';')