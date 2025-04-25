import arcpy
import pandas as pd
from arcpy.sa import *
arcpy.env.overwriteOutput = True

# Spatial Analyst availability
arcpy.CheckOutExtension("Spatial")

biophysical_table = pd.read_csv(
    r'C:\Users\ABI\OneDrive - NIVA\PhD_Work\Work\PartII\Loren\InVEST\UrbanCooling\BiophysicalTable.csv', sep =';')
print(biophysical_table)

## Now we want to simplify this biophysical table by combining bare land(1), Other paved (3), 
## and Paved road (9) into one entity called 'Imp' for impervious surfaces
landuse_clipped = "C:\\Users\\ABI\\OneDrive - NIVA\\PhD_Work\\Work\\PartII\\Loren\\LorenGIS.gdb\\landuse_clip"


# Define your mapping: original -> new class code
remap = RemapValue([
    (1, 1),   # IMP - Impervious surfaces
    (3, 1),   # IMP
    (9, 1),   # IMP
    (15, 1),  # IMP
    (6, 2),   # SVEG - Shallow vegetation
    (7, 3),   # DVEG - Deep vegetation
    (16, 4)   # BLDG - Building
])

# Apply reclassification
reclass_raster = Reclassify("landuse_clipped", "Value", remap)

# Optional: Save it
reclass_raster.save("landuse_reclass")

new_biophysical_table = {
    'lu_name': ['IMP','SVEG','DVEG','BLDG'],
    'Kc':     [0.001, 0.8, 1, 0.001],
    'green_area': [0, 1, 1, 0],
    'shade':      [0, 0, 1, 0],
    'albedo':     [0.14, 0.16, 0.2, 0.25]
}
df_bio = pd.DataFrame(new_biophysical_table)
print(df_bio)

# Create new rows for the LIDs
new_rows = pd.DataFrame([
    {
        'lu_name': 'GR5',
        'Kc': 0.5,         # assumed value for sedum
        'green_area': 1,
        'shade': 0,
        'albedo': 0.16
    },
    {
        'lu_name': 'GR20',
        'Kc': 0.6,         #assumed a bit higher 
        'green_area': 1,
        'shade': 0,
        'albedo': 0.16
    },
    {
        'lu_name': 'BC',
        'Kc': 0.9,         
        'green_area': 1,
        'shade': 0,
        'albedo': 0.16
    },
    {
        'lu_name': 'GS',
        'Kc': 0.8,          
        'green_area': 1,
        'shade': 0,
        'albedo': 0.16
    },
    {
        'lu_name': 'TRE',
        'Kc': 0.9,          
        'green_area': 1,
        'shade': 1,
        'albedo': 0.2
    }
])

# Add to original DataFrame
df_bio = pd.concat([df_bio, new_rows], ignore_index=True)

# Check result
print(df_bio)

## Determining the area of each landuse in each subcatchment
subcatchments = "C:\\Users\\ABI\\OneDrive - NIVA\\PhD_Work\\Work\\PartII\\Loren\\Data\\subcat_poly.shp"
lu_reclass = "C:\\Users\\ABI\\OneDrive - NIVA\\PhD_Work\\Work\\PartII\\Loren\\LorenGIS.gdb\\landuse_reclass"

# First convert landuse raster to a shapefile 
arcpy.RasterToPolygon_conversion(
    in_raster= lu_reclass,
    out_polygon_features= 'lu_reclass_poly',
    simplify="NO_SIMPLIFY",  
    raster_field="Value"     
),

# Intersect the landuse polygons with the subcatchments to join spatially 
arcpy.analysis.Intersect(
    in_features=['lu_reclass_poly', subcatchments],
    out_feature_class="lu_sub_intersect",
    join_attributes="ALL"
),

## Create a table that contains the subcatchment information, landuse reclass codes,
## and the area of each polygon

arcpy.management.AddField(
    in_table= "lu_sub_intersect",
    field_name="area_m2",
    field_type="DOUBLE"
)

arcpy.management.CalculateGeometryAttributes(
    in_features= "lu_sub_intersect",
    geometry_property=[["area_m2", "AREA"]],
    area_unit="SQUARE_METERS"
)
arcpy.analysis.Statistics(
    in_table="lu_sub_intersect",
    out_table="lu_sub_summary.dbf",
    statistics_fields=[["area_m2", "SUM"]],
    case_field=["SID", "gridcode"]  
),

## There are now two importable tables necessary for calculating Cooling capacity index (CC)
## Let's bring them into the code again

sub_data = "C:\\Users\\ABI\\OneDrive - NIVA\\PhD_Work\\Work\\PartII\\Loren\\lu_sub_summary.dbf"
print(df_bio)    # Biophysical table



## Convert subcatchemnt landuse dbf file into a dataframe
from dbfread import DBF
import pandas as pd

# Read DBF into a DataFrame
table = DBF(sub_data)
df_temp = pd.DataFrame(iter(table))
print(df_temp.head()),

## Change the codes in the table to text classes
# Example mapping from gridcode to lu_name
gridcode_map = {
    1: 'IMP',
    2: 'SVEG',
    3: 'DVEG',
    4: 'BLDG'
}

# Apply mapping
df_temp['lu_name'] = df_area['gridcode'].map(gridcode_map)
print(df_temp.head()),

df_area = df_temp[['SID','lu_name','SUM_area_m']]
df_area.rename(columns={ 'SUM_area_m': 'area'}, inplace=True)
print(df_area.head()),

## Combine subcatchement area data with biophysical table
df_merged = pd.merge(df_area, df_bio, on='lu_name')
print(df_merged.head(20))

## Create a column for cooling capacity index (CC) that uses an equation from InVEST Manual
## ETo or reference evapotranspiration is not considered here because since the whole area has
## only one value of ETo, it cancels out in the equation

df_merged['CC'] = 0.6 * df_merged['shade'] + 0.2 * df_merged['albedo'] + 0.2 * df_merged['Kc']

## Now, finding the total sum of CC for each landuse in each subcatchment
df_merged['CC_area'] = df_merged['CC'] * df_merged['area']
df_merged.to_csv('LU_Sub_merged')

## Now we are interested in finding the total CC in each subcatchment regardless of the landuse
df_total_cc = df_merged.groupby('SID')['CC_area'].sum().reset_index()
df_total_cc.columns = ['SID', 'cooling_capacity']
print(df_total_cc)

df = pd.read_csv(r'C:\Users\ABI\My_Files\MonteCarlo\filtered_random_LID_data_with_trees.csv', sep = ';')
print(df.head())

## Get the impervious and building areas for the base scenario for deducting later 
imp_base_areas = df_merged[df_merged['lu_name'] == 'IMP'][['SID', 'area']].copy()
bdg_base_areas = df_merged[df_merged['lu_name'] == 'BLDG'][['SID', 'area']].copy()
print(bdg_base_areas)



