# Import modules
import arcpy
from arcpy.sa import *
arcpy.env.overwriteOutput = True

# Set environment settings
arcpy.env.workspace = r"C:\Users\ABI\OneDrive - NIVA\PhD_Work\Work\PartII\Loren"

# Data imports
subcat = "C:\\Users\\ABI\\OneDrive - NIVA\\PhD_Work\\Work\\PartII\\Loren\\Data\\subcat_poly.shp"
landuse = Raster("C:\\Users\\ABI\\OneDrive - NIVA\\PhD_Work\\Work\\PartII\\Loren\\Data\\Landcover.tif")

# Create boundary of shapefile
subcat_bdy = "C:\\Users\\ABI\\OneDrive - NIVA\\PhD_Work\\Work\\PartII\\Loren\\LorenGIS.gdb\\subcat_boundary"
arcpy.management.Dissolve(subcat, subcat_bdy,["FID"],"","SINGLE_PART","DISSOLVE_LINES")

# Creating 400 m buffer of the boundary
subcat_buffer = "C:\\Users\\ABI\\OneDrive - NIVA\\PhD_Work\\Work\\PartII\\Loren\\LorenGIS.gdb\\subcat_buffer"
arcpy.analysis.Buffer(subcat_bdy, subcat_buffer,"100 Meters","FULL","ROUND","ALL")

# Clipping landuse to buffer area
landuse_clipped = ExtractByMask(landuse, subcat_buffer )

# Save the output
#landuse_clipped.save("C:\\Users\\ABI\\OneDrive - NIVA\\PhD_Work\\Work\\PartII\\Loren\\LorenGIS.gdb\\landuse_clip")

# Create a dataframe for biophysiscal table
import pandas as pd
columns = ['lucode', 'Kc', 'green_area', 'shade', 'albedo']
data = [(1,0.2,0,0,0.17),(3,0.001,0,0,0.14), (6,0.8,1,0,0.16), (7,1,1,1,0.2), (9,0.001,0,0,0.14), (15,0.001,0,0,0.2), (16,0.001,0,0,0.25)]
df = pd.DataFrame(data, columns=columns)
print(df)
df.to_csv(r'C:\Users\ABI\OneDrive - NIVA\PhD_Work\Work\PartII\Loren\InVEST\UrbanCooling\BiophysicalTable.csv', index=False, sep = ';') 

import os
import arcpy
from arcpy.sa import ExtractByMask

# Check out Spatial Analyst
arcpy.CheckOutExtension("Spatial")

# Boundary slightly larger than pixel
pixel_bdy = r"C:\Users\ABI\OneDrive - NIVA\PhD_Work\Work\PartII\Loren\LorenGIS.gdb\pixelboundary"

# Input NetCDFs
RR_nc = r"C:\Users\ABI\OneDrive - NIVA\PhD_Work\Work\PartII\Loren\Data\NGCD_RR_type2_version_24.09_20230627.nc"
TN_nc = r"C:\Users\ABI\OneDrive - NIVA\PhD_Work\Work\PartII\Loren\Data\NGCD_TN_type2_version_24.09_20230627.nc"
TX_nc = r"C:\Users\ABI\OneDrive - NIVA\PhD_Work\Work\PartII\Loren\Data\NGCD_TX_type2_version_24.09_20230627.nc"

# Output Geodatabase
gdb_path = r"C:\Users\ABI\OneDrive - NIVA\PhD_Work\Work\PartII\Loren\LorenGIS.gdb"

# Get projection from existing feature class
sr = arcpy.Describe(os.path.join(gdb_path, 'pixelboundary')).spatialReference

# Process each variable
for nc, var in zip((RR_nc, TN_nc, TX_nc), ("RR", "TN", "TX")):
    out_layer = f"{var}_layer"
    temp_raster = os.path.join(gdb_path, f"{var}_temp")
    proj_raster = os.path.join(gdb_path, f"{var}_proj")
    final_raster = os.path.join(gdb_path, f"{var}_masked")
    
    # Step 1: Create raster layer from NetCDF
    arcpy.md.MakeNetCDFRasterLayer(
        in_netCDF_file=nc,
        variable=var,
        x_dimension="X",
        y_dimension="Y",
        out_raster_layer=out_layer
    )
    
    # Step 2: Save raster layer as a permanent raster
    arcpy.management.CopyRaster(out_layer, temp_raster)
    
    # Step 3: Project raster to desired coordinate system
    arcpy.management.ProjectRaster(temp_raster, proj_raster, sr)

    # Step 4: Extract by pixel boundary using projected raster
    masked = ExtractByMask(proj_raster, pixel_bdy)
    
    # Step 5: Save final masked raster
    masked.save(final_raster)


# Get the rasters for further calculations
# The values 
P = Raster(os.path.join(gdb_path,'RR_masked'))                 # Precipitation
TN_ras = Raster(os.path.join(gdb_path,'TN_masked')) - 273      # Minimum daily temperature
TX_ras = Raster(os.path.join(gdb_path,'TX_masked')) - 273      #Maximum daily temperature

Tavg = (TN_ras + TX_ras)/2   # Tavg – the average of the daily minimum and daily maximum temperatures [°C]
TD = TX_ras - TN_ras         # TD – the difference between daily maximum and mean daily minimum temperatures [°C]
RA = 41.6                    # Extra-terrestrial radiation, estimated as 41.6 MJm-2d-1 (Zawadzka 2021)

# Reference evapotranspiration
ETo = 0.0013 * 0.408 * RA * (Tavg + 17) * (TD - 0.0123 * P)**0.76
ETo.save(os.path.join(gdb_path,'reference_ET'))

AOI = "C:\\Users\\ABI\\OneDrive - NIVA\\PhD_Work\\Work\\PartII\\Loren\\LorenGIS.gdb\\subcat_buffer"

Max_cool_dist = 100 # Assumed to be 100 m for dense urban setting

Ref_air_temp = 24

max_temp = 25.75
uhi = max_temp -  Ref_air_temp

air_bl_dist = 300


