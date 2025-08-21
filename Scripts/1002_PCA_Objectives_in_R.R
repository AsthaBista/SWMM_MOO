install.packages("corrr")
library('corrr')

install.packages("ggcorrplot")
library(ggcorrplot)

install.packages("FactoMineR")
library("FactoMineR")

install.packages("factoextra")
library("factoextra")


setwd("C:/Users/ABI/OneDrive - NIVA/Documents/GitHub/SWMM_MOO/10_Analysis")

# Check if it's set correctly
getwd()

# 3. Load your data
# Change the file path to where your CSV is stored
df <- read.csv("1000_Selected_objectives.csv", header = TRUE, sep = ";")  # skip the first label row
df <- df[-1,-1]

head(df)
df_numeric <- df[ , sapply(df, is.numeric)]   # keep only numeric cols
head(df_numeric)

data_normalized <- scale(df_numeric)
head(data_normalized)

data.pca <- princomp(data_normalized)
summary(data.pca)

data.pca$loadings[, 1:2]

fviz_eig(data.pca, addlabels = TRUE)

# --- add these if not installed yet ---
install.packages("plotly")
# Each point is an objective (a column in your data)
# PC1 vs PC2
fviz_pca_var(data.pca, axes = c(1, 2), repel = TRUE,
             col.var = "black", title = "Objectives: PC1 vs PC2")

# PC2 vs PC3
fviz_pca_var(data.pca, axes = c(2, 3), repel = TRUE,
             col.var = "black", title = "Objectives: PC2 vs PC3")

# PC1 vs PC3
fviz_pca_var(data.pca, axes = c(1, 3), repel = TRUE,
             col.var = "black", title = "Objectives: PC1 vs PC3")

# Extract loadings as a regular numeric matrix
loadings <- unclass(data.pca$loadings)

# Convert to data frame, keep objective names
loadings_df <- as.data.frame(loadings)
loadings_df$Objective <- rownames(loadings_df)

# Reorder so Objective is first column
loadings_df <- loadings_df[, c(ncol(loadings_df), 1:(ncol(loadings_df)-1))]

# Write to CSV
write.table(loadings_df, "PCA_Loadings_selected.csv",
            row.names = FALSE, sep = ";", dec = ".", quote = TRUE)





