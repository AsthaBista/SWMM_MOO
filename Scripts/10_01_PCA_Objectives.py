# -*- coding: utf-8 -*-
"""
Created on Wed Aug 13 11:03:09 2025

@author: ABI
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import seaborn as sns

# -----------------------
# 1. Load and prepare data
# -----------------------

# Replace with your own file path
file_path = r"C:\Users\ABI\OneDrive - NIVA\Documents\GitHub\SWMM_MOO\10_Analysis\1000_Normalized_objectives.csv"

# Read CSV (semicolon-separated in your case)
# The header row is at index 1 (because row 0 contains original variable labels)
df = pd.read_csv(file_path, sep=";", header=1)

# Keep only numeric columns (drop ID column)
df_num = df.drop(columns=["sim_number"])

# Convert to numeric (in case some are strings)
#df_num = df_num.apply(pd.to_numeric, errors="coerce")

# OPTIONAL: Flip Temp so that higher values mean more cooling benefit
#df_num["Temp"] = 1 - df_num["Temp"]

# -----------------------
# 2. Standardize data
# -----------------------
# PCA works best if each variable has mean = 0 (and often variance = 1),
# but since your data is already normalized [0,1], we only mean-center.
X_scaled = StandardScaler(with_mean=True, with_std=False).fit_transform(df_num)

# -----------------------
# 3. Run PCA
# -----------------------
pca = PCA()
pca_components = pca.fit_transform(X_scaled)  # Transformed coordinates of observations
explained_variance = pca.explained_variance_ratio_  # % variance explained by each PC
loadings = pca.components_.T  # Contribution of each variable to each PC

# -----------------------
# 4. Explained variance plot
# -----------------------
plt.figure(figsize=(8, 5))
plt.plot(range(1, len(explained_variance) + 1),
         np.cumsum(explained_variance) * 100,
         marker='o')
plt.xlabel("Number of Principal Components")
plt.ylabel("Cumulative Explained Variance (%)")
plt.title("PCA - Cumulative Explained Variance")
plt.grid(True)
plt.show()
# Save the plot
plt.savefig(r"C:\Users\ABI\OneDrive - NIVA\Documents\GitHub\SWMM_MOO\10_Analysis\1002_PCA\1002_pca_explained_variance.png", dpi=300, bbox_inches="tight")

# Create a table of explained variance
variance_table = pd.DataFrame({
    "PC": range(1, len(explained_variance) + 1),
    "Explained Variance (%)": explained_variance * 100,
    "Cumulative Variance (%)": np.cumsum(explained_variance) * 100
})

# Save table to CSV
variance_table.to_csv(r"C:\Users\ABI\OneDrive - NIVA\Documents\GitHub\SWMM_MOO\10_Analysis\1002_PCA\1002_pca_variance_table.csv",sep=";",index=False)

print("PCA variance table saved as pca_variance_table.csv")
print(variance_table)

# -----------------------
# 5. PCA Biplot
# -----------------------
# Biplot shows observations in PC space + variable vectors (loadings)

pc1 = pca_components[:, 0]
pc2 = pca_components[:, 1]

plt.figure(figsize=(10, 8))
# Scatter plot of observations
plt.scatter(pc1, pc2, alpha=0.6, label="Observations")

# Add variable vectors (loadings scaled for visualization)
for i, var in enumerate(df_num.columns):
    plt.arrow(0, 0,
              loadings[i, 0] * 3, loadings[i, 1] * 3,  # scale factor for readability
              color='r', alpha=0.7, head_width=0.05)
    plt.text(loadings[i, 0] * 3.2,
             loadings[i, 1] * 3.2,
             var, color='r', ha='center', va='center')

plt.axhline(0, color='grey', lw=1)
plt.axvline(0, color='grey', lw=1)
plt.xlabel(f"PC1 ({explained_variance[0]*100:.1f}% var)")
plt.ylabel(f"PC2 ({explained_variance[1]*100:.1f}% var)")
plt.title("PCA Biplot")
plt.legend()
plt.grid(True)
plt.show()


# from mpl_toolkits.mplot3d import Axes3D  # Needed for 3D plotting

# # First 3 PCs
# pc1 = pca_components[:, 0]
# pc2 = pca_components[:, 1]
# pc3 = pca_components[:, 2]

# fig = plt.figure(figsize=(10, 8))
# ax = fig.add_subplot(111, projection='3d')

# # Scatter plot
# ax.scatter(pc1, pc2, pc3, c='blue', alpha=0.6)

# # Labels
# ax.set_xlabel(f"PC1 ({explained_variance[0]*100:.1f}% var)")
# ax.set_ylabel(f"PC2 ({explained_variance[1]*100:.1f}% var)")
# ax.set_zlabel(f"PC3 ({explained_variance[2]*100:.1f}% var)")
# ax.set_title("3D PCA Scatter Plot")

# plt.show()

# Create DataFrame of loadings
loadings_df = round(pd.DataFrame(
    pca.components_.T,                # Transpose so rows = variables
    columns=[f"PC{i+1}" for i in range(len(pca.components_))],
    index=df_num.columns               # Variable names
),4)

# Save loadings to CSV
loadings_df.to_csv(
    r"C:\Users\ABI\OneDrive - NIVA\Documents\GitHub\SWMM_MOO\10_Analysis\1002_PCA\1002_pca_loadings.csv",
    sep=";",
    index=True
)

print("PCA loadings saved as pca_loadings.csv")
print(loadings_df)
