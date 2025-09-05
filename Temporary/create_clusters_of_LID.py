# Dual Cluster Analysis: Green Roofs vs Terrain LIDs
# Author: [Your Name]

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

# Set plotting style
plt.style.use('default')
sns.set_palette("viridis")
plt.rcParams['figure.figsize'] = (10, 6)

# Load and preprocess data
df = pd.read_csv(r'C:\Users\ABI\OneDrive - NIVA\Documents\GitHub\SWMM_MOO\01_Preprocessing\0103_Data_cleaned_random_generated_scenarios.csv', sep=';')

def extract_lid_data(df):
    """Extract both green roof and terrain LID data"""
    result_df = pd.DataFrame()
    result_df['sim'] = df['sim']
    result_df['GR_Type'] = df['Type']  # GR5 or GR20
    
    # Green Roof area (S1-S4)
    green_roof_columns = ['S1', 'S2', 'S3', 'S4']
    result_df['Total_GR_Area'] = df[green_roof_columns].sum(axis=1)
    
    # Terrain LIDs (S5, S7-S11)
    lid_types = ['GS', 'TRE', 'BC']
    for lid in lid_types:
        area_columns = []
        for i in (5, 7, 8, 9, 10, 11):
            type_col = f'S{i}_Type'
            area_col = f'S{i}'
            area_series = df[area_col].where(df[type_col] == lid, 0)
            area_columns.append(area_series)
        
        result_df[f'Total_{lid}_Area'] = pd.concat(area_columns, axis=1).sum(axis=1)
    
    # Calculate percentages for terrain LIDs
    terrain_area_cols = [f'Total_{lid}_Area' for lid in lid_types]
    result_df['Total_Terrain_Area'] = result_df[terrain_area_cols].sum(axis=1)
    
    for lid in lid_types:
        result_df[f'Pct_{lid}'] = result_df[f'Total_{lid}_Area'] / result_df['Total_Terrain_Area']
    
    result_df.fillna(0, inplace=True)
    return result_df

# Extract data
cluster_df = extract_lid_data(df)

# ----------------------------
# 1. GREEN ROOF CLUSTERING (by type: GR5 vs GR20)
# ----------------------------
print("1. Green Roof Clustering (by type)...")

# Simple classification based on GR_Type
cluster_df['GR_Cluster'] = cluster_df['GR_Type'].map({'GR5': 'GR5', 'GR20': 'GR20'})

gr_cluster_summary = cluster_df.groupby('GR_Cluster').agg({
    'Total_GR_Area': ['mean', 'count']
}).round(0)

gr_cluster_summary.columns = ['Avg_GR_Area', 'Count']
print("Green Roof Cluster Summary:")
print(gr_cluster_summary)

# ----------------------------
# 2. TERRAIN LID CLUSTERING
# ----------------------------
print("\n2. Terrain LID Clustering...")

# Prepare terrain LID data for clustering
X_terrain = cluster_df[['Pct_GS', 'Pct_TRE', 'Pct_BC']].values
scaler = StandardScaler()
X_terrain_scaled = scaler.fit_transform(X_terrain)

# Use 3 clusters for terrain LIDs
kmeans_terrain = KMeans(n_clusters=3, random_state=42, n_init=20)
terrain_clusters = kmeans_terrain.fit_predict(X_terrain_scaled)
cluster_df['Terrain_Cluster'] = terrain_clusters

# Analyze terrain clusters
terrain_cluster_summary = cluster_df.groupby('Terrain_Cluster').agg({
    'Pct_GS': 'mean',
    'Pct_TRE': 'mean', 
    'Pct_BC': 'mean',
    'Total_Terrain_Area': 'mean',
    'sim': 'count'
}).rename(columns={'sim': 'Count'}).round(3)

print("Terrain Cluster Summary:")
print(terrain_cluster_summary)

# ----------------------------
# 3. VISUALIZATION: Terrain LID Composition
# ----------------------------
plt.figure(figsize=(10, 6))
cluster_comp = terrain_cluster_summary[['Pct_GS', 'Pct_TRE', 'Pct_BC']]
cluster_comp.plot(kind='bar', stacked=True)
plt.title('Terrain LID Composition by Cluster')
plt.ylabel('Percentage of Terrain LID Area')
plt.xlabel('Terrain Cluster')
plt.xticks(rotation=0)
plt.legend(['Green Space', 'Trees', 'Bioretention Cells'])
plt.grid(axis='y', alpha=0.3)
plt.tight_layout()
plt.savefig('terrain_cluster_composition.png', dpi=300, bbox_inches='tight')
plt.show()

# ----------------------------
# 4. RENUMBER CLUSTERS AND CREATE FINAL TABLE
# ----------------------------
# Update cluster numbering from 0,1,2 to 1,2,3
cluster_df['Terrain_Cluster'] = cluster_df['Terrain_Cluster'] + 1

# Create final results table
results_table = cluster_df[['sim', 'GR_Type', 'GR_Cluster', 'Terrain_Cluster', 
                           'Total_GR_Area', 'Total_Terrain_Area']].copy()

# Add cluster interpretations based on your visualization
terrain_cluster_names = {
    1: "Tree-Heavy Terrain",
    2: "GS-Heavy Terrain", 
    3: "BC-Heavy Terrain"
}

results_table['Terrain_Cluster_Name'] = results_table['Terrain_Cluster'].map(terrain_cluster_names)
results_table['GR_Cluster_Name'] = results_table['GR_Cluster'].map({'GR5': '5cm Green Roof', 'GR20': '20cm Green Roof'})

print("\n3. Sample of Final Results Table:")
print(results_table.head(10))

print(f"\nTotal scenarios: {len(results_table)}")
print(f"Green Roof types: {results_table['GR_Cluster'].value_counts().to_dict()}")
print(f"Terrain clusters: {results_table['Terrain_Cluster'].value_counts().to_dict()}")

# ----------------------------
# 5. CROSS-TABULATION ANALYSIS
# ----------------------------
print("\n4. Cross-tabulation of GR Type vs Terrain Cluster:")
cross_tab = pd.crosstab(results_table['GR_Cluster'], results_table['Terrain_Cluster_Name'])
print(cross_tab)

# Save comprehensive results with your preferred format
results_table.to_csv(r'C:\Users\ABI\OneDrive - NIVA\Documents\GitHub\SWMM_MOO\10_Analysis\scenario_cluster_assignments.csv', 
                     index=False, sep=';')

print("\nResults saved to: C:\\Users\\ABI\\OneDrive - NIVA\\Documents\\GitHub\\SWMM_MOO\\10_Analysis\\scenario_cluster_assignments.csv")

# ----------------------------
# 6. CLUSTER INTERPRETATIONS
# ----------------------------
print("\n5. Cluster Interpretations:")
print("\nGreen Roof Clusters:")
print("- GR5: 5cm substrate green roofs")
print("- GR20: 20cm substrate green roofs")

print("\nTerrain Clusters:")
print("1. Tree-Heavy Terrain: Dominated by trees")
print("2. GS-Heavy Terrain: Dominated by grassed areas/green space") 
print("3. BC-Heavy Terrain: Dominated by bioretention cells")

# Detailed composition for each terrain cluster
print("\nDetailed Terrain Cluster Composition:")
terrain_cluster_summary_renumbered = cluster_df.groupby('Terrain_Cluster').agg({
    'Pct_GS': 'mean',
    'Pct_TRE': 'mean', 
    'Pct_BC': 'mean',
    'Total_Terrain_Area': 'mean',
    'sim': 'count'
}).rename(columns={'sim': 'Count'}).round(3)

print(terrain_cluster_summary_renumbered)