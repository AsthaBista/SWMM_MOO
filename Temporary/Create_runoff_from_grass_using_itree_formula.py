# -*- coding: utf-8 -*-
"""
Created on Fri Jun  6 08:58:45 2025

@author: ABI
"""

import pandas as pd
import numpy as np

# Load climate data
df = pd.read_csv(r"C:\Users\ABI\OneDrive - NIVA\PhD_Work\Work\PartII\Loren\Climate_cleaned_data.csv", delimiter=';')
df.rename(columns={
    'Date': 'date',
    'Rain(mm)': 'rainfall_mm',
    'Max': 'Tmax',
    'Min': 'Tmin'
}, inplace=True)
df['date'] = pd.to_datetime(df['date'], dayfirst=True)
df['Tavg'] = (df['Tmax'] + df['Tmin']) / 2

# PE using Hargreaves
Ra_factor = 0.0023 * 15
df['PE_mm'] = Ra_factor * (df['Tavg'] + 17.8) * np.sqrt(df['Tmax'] - df['Tmin'])
df['PE_m'] = df['PE_mm'] / 1000

# Constants
AREA_M2 = 10
Simax_grass = 0.0015  # 1.5 mm depression storage
Simax_bare = 0.0005   # 0.5 mm for bare soil

# Initial storage
S_grass = 0.0
S_bare = 0.0

results = []

for _, row in df.iterrows():
    P = row['rainfall_mm'] / 1000
    PE = row['PE_m']

    # -- Grass patch --
    Eg = (S_grass / Simax_grass) * PE if Simax_grass > 0 else 0
    Eg = min(Eg, S_grass)
    Rg = max(P - (Simax_grass - S_grass) - Eg, 0)
    S_grass = min(S_grass + P - Eg, Simax_grass)

    # -- Bare soil patch --
    Eb = (S_bare / Simax_bare) * PE if Simax_bare > 0 else 0
    Eb = min(Eb, S_bare)
    Rb = max(P - (Simax_bare - S_bare) - Eb, 0)
    S_bare = min(S_bare + P - Eb, Simax_bare)

    results.append({
        "date": row['date'],
        "rain_mm": row['rainfall_mm'],
        "PE_mm": row['PE_mm'],
        "runoff_grass_mm": Rg * 1000,
        "runoff_bare_mm": Rb * 1000,
        "evap_grass_mm": Eg * 1000,
        "evap_bare_mm": Eb * 1000
    })

# To DataFrame
runoff_df = pd.DataFrame(results)
runoff_df['month'] = runoff_df['date'].dt.month
runoff_df['year'] = runoff_df['date'].dt.year

# Filter May–October
season_df = runoff_df[(runoff_df['month'] >= 5) & (runoff_df['month'] <= 10)]

# Annual sums
annual = season_df.drop(columns=['date', 'month']).groupby('year').sum()

# Convert runoff from mm to liters
annual['runoff_grass_L'] = annual['runoff_grass_mm'] * AREA_M2
annual['runoff_bare_L'] = annual['runoff_bare_mm'] * AREA_M2
annual['reduction_L'] = annual['runoff_bare_L'] - annual['runoff_grass_L']

# Save results
annual.to_csv(r"C:\Users\ABI\OneDrive - NIVA\PhD_Work\Work\PartII\Loren\grass_vs_nograss_runoff.csv", sep=';')
