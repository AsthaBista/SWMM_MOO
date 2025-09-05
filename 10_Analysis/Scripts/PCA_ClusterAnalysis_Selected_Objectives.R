# Load required libraries
library(ggplot2)
library(ggfortify)
library(factoextra)
library(dplyr)
library(tidyr)
library(corrplot)
library(cluster)
library(FactoMineR)
library(GGally)

# 1. Read and preprocess data
my_data <- read.csv("1000_Selected_Objectives.csv", sep=";")

# Remove first row (all zeros) and convert to numeric
my_data <- my_data[-1, ]
my_data[] <- lapply(my_data, as.numeric)

# Check data structure
cat("Data dimensions:", dim(my_data), "\n")
cat("Column names:", names(my_data), "\n\n")
cat("Objectives: PR20, TR, BGF, Inv, UNA, TSS\n")

# 2. Basic descriptive statistics
cat("Descriptive Statistics:\n")
print(summary(my_data))

# 3. Check for missing values
cat("\nMissing values per column:\n")
print(colSums(is.na(my_data)))

# 4. Correlation analysis
cor_matrix <- cor(my_data)
cat("\nCorrelation Matrix:\n")
print(round(cor_matrix, 2))

# Visualize correlation matrix
png("Correlation_Matrix.png", width = 8, height = 6, units = "in", res = 300)
corrplot(cor_matrix, method = "color", type = "upper", 
         order = "hclust", tl.cex = 0.8, tl.col = "black",
         title = "Correlation Matrix of Objectives",
         mar = c(0, 0, 1, 0))
dev.off()

# 5. Scatterplot matrix for visual correlation assessment
scatter_matrix <- ggpairs(my_data, 
                          title = "Scatterplot Matrix of Objectives",
                          lower = list(continuous = "smooth"),
                          diag = list(continuous = "barDiag")) +
  theme_minimal()

ggsave("Scatterplot_Matrix.png", scatter_matrix, width = 12, height = 10, dpi = 300)

# 6. Scale the data for PCA
my_data_scaled <- scale(my_data)

# 7. Perform PCA
pca_result <- prcomp(my_data_scaled, center = TRUE, scale. = TRUE)

# PCA summary
cat("\nPCA Summary:\n")
print(summary(pca_result))

# 8. Scree plot to determine number of components to retain
scree_plot <- fviz_eig(pca_result, addlabels = TRUE, 
                       main = "Scree Plot - Variance Explained by Principal Components",
                       barfill = "steelblue", barcolor = "steelblue",
                       linecolor = "darkred") +
  theme_minimal()

ggsave("PCA_Scree_Plot.png", scree_plot, width = 8, height = 6, dpi = 300)

# 9. Variable factor map - shows how objectives relate to PCs
var_plot <- fviz_pca_var(pca_result,
                         col.var = "contrib",
                         gradient.cols = c("#00AFBB", "#E7B800", "#FC4E07"),
                         repel = TRUE,
                         title = "PCA - Variable Factor Map") +
  theme_minimal()

ggsave("PCA_Variable_Map.png", var_plot, width = 10, height = 8, dpi = 300)

# 10. Contributions of variables to principal components
# Contributions to PC1
contrib_pc1 <- fviz_contrib(pca_result, choice = "var", axes = 1, top = 6,
                            title = "Contributions of Objectives to PC1") +
  theme_minimal()

# Contributions to PC2
contrib_pc2 <- fviz_contrib(pca_result, choice = "var", axes = 2, top = 6,
                            title = "Contributions of Objectives to PC2") +
  theme_minimal()

# Contributions to PC3
contrib_pc3 <- fviz_contrib(pca_result, choice = "var", axes = 3, top = 6,
                            title = "Contributions of Objectives to PC3") +
  theme_minimal()

# Contributions to PC4
contrib_pc4 <- fviz_contrib(pca_result, choice = "var", axes = 4, top = 6,
                            title = "Contributions of Objectives to PC4") +
  theme_minimal()


ggsave("PCA_Contributions_PC1.png", contrib_pc1, width = 10, height = 6, dpi = 300)
ggsave("PCA_Contributions_PC2.png", contrib_pc2, width = 10, height = 6, dpi = 300)
ggsave("PCA_Contributions_PC3.png", contrib_pc3, width = 10, height = 6, dpi = 300)
ggsave("PCA_Contributions_PC4.png", contrib_pc4, width = 10, height = 6, dpi = 300)

# 11. Extract PCA loadings for interpretation
pca_loadings <- as.data.frame(pca_result$rotation[, 1:2])
pca_loadings$Objective <- rownames(pca_loadings)
pca_loadings$PC1_abs <- abs(pca_loadings$PC1)
pca_loadings$PC2_abs <- abs(pca_loadings$PC2)

cat("\nPCA Loadings (First 2 Components):\n")
print(pca_loadings)

# 12. Cluster analysis on objectives based on PCA loadings
# Calculate distance matrix between objectives
obj_distance <- dist(t(my_data_scaled))  # Transpose to cluster objectives

# Hierarchical clustering
hc <- hclust(obj_distance, method = "ward.D2")

# Dendrogram
dendro_plot <- fviz_dend(hc, k = 3, 
                         cex = 0.8,
                         k_colors = c("#2E9FDF", "#00AFBB", "#E7B800"),
                         color_labels_by_k = TRUE,
                         rect = TRUE,
                         main = "Cluster Dendrogram of Objectives",
                         xlab = "Objectives", ylab = "Height")

ggsave("Cluster_Dendrogram.png", dendro_plot, width = 10, height = 6, dpi = 300)

# 13. Determine optimal number of clusters (adjusted for 6 objectives)
# Since we only have 6 objectives, we'll test up to 5 clusters
max_clusters <- min(5, ncol(my_data_scaled) - 1)  # Maximum of 5 or n-1

# Elbow method
elbow_plot <- fviz_nbclust(t(my_data_scaled), kmeans, method = "wss", k.max = max_clusters) +
  ggtitle("Elbow Method for Optimal Number of Clusters") +
  theme_minimal()

# Silhouette method
silhouette_plot <- fviz_nbclust(t(my_data_scaled), kmeans, method = "silhouette", k.max = max_clusters) +
  ggtitle("Silhouette Method for Optimal Number of Clusters") +
  theme_minimal()

ggsave("Elbow_Method.png", elbow_plot, width = 8, height = 6, dpi = 300)
ggsave("Silhouette_Method.png", silhouette_plot, width = 8, height = 6, dpi = 300)

# 14. K-means clustering on objectives
# Based on your objectives and typical patterns, let's try 2-3 clusters
set.seed(123)

# Try different cluster numbers and choose the best
best_clusters <- 2  # Start with 2 clusters for 6 objectives

# Check silhouette scores to choose optimal k
if(max_clusters >= 2) {
  silhouette_scores <- numeric(max_clusters - 1)
  for(k in 2:max_clusters) {
    kmeans_temp <- kmeans(t(my_data_scaled), centers = k, nstart = 25)
    sil <- silhouette(kmeans_temp$cluster, dist(t(my_data_scaled)))
    silhouette_scores[k-1] <- mean(sil[, 3])
  }
  best_clusters <- which.max(silhouette_scores) + 1
  cat("Optimal number of clusters based on silhouette:", best_clusters, "\n")
}

kmeans_result <- kmeans(t(my_data_scaled), centers = best_clusters, nstart = 25)

cat("\nK-means Cluster Membership:\n")
cluster_membership <- data.frame(Objective = names(kmeans_result$cluster),
                                 Cluster = kmeans_result$cluster)
print(cluster_membership)

# 15. Visualize clusters in PCA space
cluster_plot <- fviz_cluster(list(data = t(my_data_scaled), cluster = kmeans_result$cluster),
                             palette = c("#2E9FDF", "#00AFBB", "#E7B800", "#FC4E07", "#999999")[1:best_clusters], 
                             geom = "point",
                             ellipse.type = "convex",
                             repel = TRUE,
                             main = paste("Cluster Plot of Objectives (k =", best_clusters, ")"),
                             ggtheme = theme_minimal())

ggsave("Cluster_Plot.png", cluster_plot, width = 10, height = 8, dpi = 300)

# 16. Save all results
write.csv(cor_matrix, "Correlation_Matrix_Results.csv")
write.csv(pca_loadings, "PCA_Loadings_Results.csv")
write.csv(cluster_membership, "Cluster_Membership_Results.csv")

# 17. Interpretation summary
cat("\n=== INTERPRETATION GUIDE ===\n")
cat("1. Check correlation matrix for strong relationships (>0.7 or <-0.7)\n")
cat("2. Look at PCA variable map - objectives close together are correlated\n")
cat("3. Objectives with high contributions to same PC can be grouped\n")
cat("4. Cluster analysis shows which objectives behave similarly\n")
cat("5. Consider both statistical and domain knowledge for final grouping\n")

cat("\nAnalysis complete! Check the generated plots and CSV files for results.\n")