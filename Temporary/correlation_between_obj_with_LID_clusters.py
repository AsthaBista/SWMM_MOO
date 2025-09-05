# Focused Analysis: LID Types vs Runoff Reduction
# Author: [Your Name]

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import pearsonr
import warnings
warnings.filterwarnings('ignore')

# Set plotting style
plt.style.use('default')
plt.rcParams['figure.figsize'] = (12, 10)
plt.rcParams['font.size'] = 12

# ----------------------------
# 1. LOAD AND PREPARE DATA
# ----------------------------

print("Loading data...")

# Define the base directory
base_dir = r'C:\Users\ABI\OneDrive - NIVA\Documents\GitHub\SWMM_MOO\10_Analysis'

# Load objectives data
obj_df = pd.read_csv(f'{base_dir}\\1000_Selected_Objectives.csv', sep=';')

# Load cluster assignments
cluster_df = pd.read_csv(f'{base_dir}\\scenario_cluster_assignments.csv', sep=';')

# Rename objectives for clarity
obj_df.rename(columns={
    'PR20': 'Peak_Runoff_Reduction',
    'TR': 'Total_Runoff_Reduction', 
    'BGF': 'Blue_Green_Factor',
    'Inv': 'Investment_Cost',
    'UNA': 'Urban_Nature_Access',
    'TSS': 'TSS_Reduction'
}, inplace=True)

# Merge objectives with cluster assignments
merged_df = pd.merge(cluster_df, obj_df, left_on='sim', right_index=True)

# Remove baseline scenario if needed
merged_df = merged_df[merged_df['Peak_Runoff_Reduction'] > 0]

print(f"Analyzing {len(merged_df)} scenarios with LID implementations")

# ----------------------------
# 2. GREEN ROOF AREA vs RUNOFF REDUCTION
# ----------------------------

print("\n2. Green Roof Area vs Runoff Reduction Analysis...")

# Calculate correlation between green roof area and runoff reduction
gr_area = merged_df['Total_GR_Area']
peak_reduction = merged_df['Peak_Runoff_Reduction']
total_reduction = merged_df['Total_Runoff_Reduction']

r_peak_gr, p_peak_gr = pearsonr(gr_area, peak_reduction)
r_total_gr, p_total_gr = pearsonr(gr_area, total_reduction)

print(f"Green Roof Area vs Peak Runoff Reduction: r = {r_peak_gr:.3f}, p = {p_peak_gr:.2e}")
print(f"Green Roof Area vs Total Runoff Reduction: r = {r_total_gr:.3f}, p = {p_total_gr:.2e}")

# Plot Green Roof Area vs Runoff Reduction
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

# Peak Runoff Reduction
scatter1 = ax1.scatter(gr_area, peak_reduction, alpha=0.7, s=50, c='blue')
ax1.set_xlabel('Green Roof Area (m²)')
ax1.set_ylabel('Peak Runoff Reduction')
ax1.set_title(f'Green Roof Area vs Peak Runoff Reduction\nr = {r_peak_gr:.3f}, p = {p_peak_gr:.2e}')
ax1.grid(True, alpha=0.3)

# Total Runoff Reduction
scatter2 = ax2.scatter(gr_area, total_reduction, alpha=0.7, s=50, c='green')
ax2.set_xlabel('Green Roof Area (m²)')
ax2.set_ylabel('Total Runoff Reduction')
ax2.set_title(f'Green Roof Area vs Total Runoff Reduction\nr = {r_total_gr:.3f}, p = {p_total_gr:.2e}')
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(f'{base_dir}\\green_roof_vs_runoff_reduction.png', dpi=300, bbox_inches='tight')
plt.show()

# ----------------------------
# 3. TERRAIN LID AREA vs RUNOFF REDUCTION
# ----------------------------

print("\n3. Terrain LID Area vs Runoff Reduction Analysis...")

# Calculate correlation between terrain LID area and runoff reduction
terrain_area = merged_df['Total_Terrain_Area']

r_peak_terrain, p_peak_terrain = pearsonr(terrain_area, peak_reduction)
r_total_terrain, p_total_terrain = pearsonr(terrain_area, total_reduction)

print(f"Terrain LID Area vs Peak Runoff Reduction: r = {r_peak_terrain:.3f}, p = {p_peak_terrain:.2e}")
print(f"Terrain LID Area vs Total Runoff Reduction: r = {r_total_terrain:.3f}, p = {p_total_terrain:.2e}")

# Plot Terrain LID Area vs Runoff Reduction
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

# Peak Runoff Reduction
scatter1 = ax1.scatter(terrain_area, peak_reduction, alpha=0.7, s=50, c='red')
ax1.set_xlabel('Terrain LID Area (m²)')
ax1.set_ylabel('Peak Runoff Reduction')
ax1.set_title(f'Terrain LID Area vs Peak Runoff Reduction\nr = {r_peak_terrain:.3f}, p = {p_peak_terrain:.2e}')
ax1.grid(True, alpha=0.3)

# Total Runoff Reduction
scatter2 = ax2.scatter(terrain_area, total_reduction, alpha=0.7, s=50, c='purple')
ax2.set_xlabel('Terrain LID Area (m²)')
ax2.set_ylabel('Total Runoff Reduction')
ax2.set_title(f'Terrain LID Area vs Total Runoff Reduction\nr = {r_total_terrain:.3f}, p = {p_total_terrain:.2e}')
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(f'{base_dir}\\terrain_lid_vs_runoff_reduction.png', dpi=300, bbox_inches='tight')
plt.show()

# ----------------------------
# 4. SPECIFIC LID TYPES vs RUNOFF REDUCTION
# ----------------------------

print("\n4. Specific LID Types vs Runoff Reduction Analysis...")

# Calculate correlations for each LID type
lid_types = ['Total_GS_Area', 'Total_TRE_Area', 'Total_BC_Area']
lid_names = ['Green Space', 'Trees', 'Bioretention Cells']

results = []
for lid_type, lid_name in zip(lid_types, lid_names):
    lid_area = merged_df[lid_type]
    
    r_peak, p_peak = pearsonr(lid_area, peak_reduction)
    r_total, p_total = pearsonr(lid_area, total_reduction)
    
    results.append({
        'LID_Type': lid_name,
        'Area_Column': lid_type,
        'Peak_r': r_peak,
        'Peak_p': p_peak,
        'Total_r': r_total,
        'Total_p': p_total
    })
    
    print(f"{lid_name} vs Peak Runoff Reduction: r = {r_peak:.3f}, p = {p_peak:.2e}")
    print(f"{lid_name} vs Total Runoff Reduction: r = {r_total:.3f}, p = {p_total:.2e}")
    print()

# Create summary dataframe
lid_corr_df = pd.DataFrame(results)
print("Summary of LID Type Correlations with Runoff Reduction:")
print(lid_corr_df.round(3))

# Plot individual LID types
fig, axes = plt.subplots(2, 3, figsize=(18, 12))

for i, (lid_type, lid_name) in enumerate(zip(lid_types, lid_names)):
    lid_area = merged_df[lid_type]
    
    # Peak Runoff Reduction
    ax1 = axes[0, i]
    scatter1 = ax1.scatter(lid_area, peak_reduction, alpha=0.7, s=50, c=f'C{i}')
    r_peak, p_peak = pearsonr(lid_area, peak_reduction)
    ax1.set_xlabel(f'{lid_name} Area (m²)')
    ax1.set_ylabel('Peak Runoff Reduction')
    ax1.set_title(f'{lid_name} vs Peak Runoff Reduction\nr = {r_peak:.3f}, p = {p_peak:.2e}')
    ax1.grid(True, alpha=0.3)
    
    # Total Runoff Reduction
    ax2 = axes[1, i]
    scatter2 = ax2.scatter(lid_area, total_reduction, alpha=0.7, s=50, c=f'C{i}')
    r_total, p_total = pearsonr(lid_area, total_reduction)
    ax2.set_xlabel(f'{lid_name} Area (m²)')
    ax2.set_ylabel('Total Runoff Reduction')
    ax2.set_title(f'{lid_name} vs Total Runoff Reduction\nr = {r_total:.3f}, p = {p_total:.2e}')
    ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(f'{base_dir}\\specific_lid_types_vs_runoff_reduction.png', dpi=300, bbox_inches='tight')
plt.show()

# ----------------------------
# 5. COST-EFFECTIVENESS ANALYSIS
# ----------------------------

print("\n5. Cost-Effectiveness Analysis...")

# Calculate runoff reduction per unit area
merged_df['Peak_Reduction_per_m2'] = merged_df['Peak_Runoff_Reduction'] / (merged_df['Total_GR_Area'] + merged_df['Total_Terrain_Area'])
merged_df['Total_Reduction_per_m2'] = merged_df['Total_Runoff_Reduction'] / (merged_df['Total_GR_Area'] + merged_df['Total_Terrain_Area'])

# Group by terrain cluster and calculate efficiency
efficiency_by_terrain = merged_df.groupby('Terrain_Cluster_Name').agg({
    'Peak_Reduction_per_m2': 'mean',
    'Total_Reduction_per_m2': 'mean',
    'Total_GR_Area': 'mean',
    'Total_Terrain_Area': 'mean'
}).round(4)

print("Runoff Reduction Efficiency by Terrain Cluster (per m² of LID area):")
print(efficiency_by_terrain)

# ----------------------------
# 6. SAVE RESULTS
# ----------------------------

# Save correlation results
lid_corr_df.to_csv(f'{base_dir}\\lid_runoff_correlations.csv', sep=';', index=False)
efficiency_by_terrain.to_csv(f'{base_dir}\\runoff_efficiency_by_terrain.csv', sep=';')

print("\nAnalysis complete! Files saved:")
print("✓ green_roof_vs_runoff_reduction.png")
print("✓ terrain_lid_vs_runoff_reduction.png")
print("✓ specific_lid_types_vs_runoff_reduction.png")
print("✓ lid_runoff_correlations.csv")
print("✓ runoff_efficiency_by_terrain.csv")

print("\nKey Findings:")
print(f"Green Roof Area correlation with runoff reduction: r = {r_total_gr:.3f}")
print(f"Terrain LID Area correlation with runoff reduction: r = {r_total_terrain:.3f}")
print("Specific LID type correlations provide insights into which strategies are most effective")