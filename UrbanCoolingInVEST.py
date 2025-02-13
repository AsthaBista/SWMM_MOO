from osgeo import gdal
gdal.UseExceptions()
import natcap.invest.urban_cooling_model
import time

# Define the arguments dictionary with required parameters
args = {
    'workspace_dir': r'C:\Users\ABI\My_Files\ES_Quantification\UrbanCooling',
    'lulc_raster_path': r'C:\Users\ABI\My_Files\ES_Quantification\UrbanCooling\LandcoverBigarea.tif',
    'ref_eto_raster_path': r'C:\Users\ABI\My_Files\ES_Quantification\UrbanCooling\E0_20240627.tif',
    'aoi_vector_path': r'C:\Users\ABI\My_Files\ES_Quantification\UrbanCooling\BigAreaboundary.shp',
    'biophysical_table_path': r'C:\Users\ABI\My_Files\ES_Quantification\UrbanCooling\BiophysicalTable.csv',
    'green_area_cooling_distance': 400.0,
    't_air_average_radius': 500,
    'uhi_max': 0.2,
    't_ref': 26.5,
    'cc_method': 'factors',
    'cc_weight_shade': 0.6,
    'cc_weight_albedo': 0.2,
    'cc_weight_eti': 0.2,
    'do_energy_valuation': False,
    'do_productivity_valuation': False,
}

# Progress logger
def progress_logger(step, total_steps, message):
    percent_complete = (step / total_steps) * 100
    print(f"[{percent_complete:.2f}%] {message}")

# Execute with progress tracking
def execute_with_progress(args):
    total_steps = 5  # Estimate of logical steps in the process
    print("Starting Urban Cooling Model...")

    progress_logger(1, total_steps, "Validating inputs")
    time.sleep(1)  # Simulate work

    progress_logger(2, total_steps, "Processing land cover data")
    time.sleep(2)  # Simulate work

    progress_logger(3, total_steps, "Calculating cooling effect")
    natcap.invest.urban_cooling_model.execute(args)  # Execute the main model

    progress_logger(4, total_steps, "Finalizing results")
    time.sleep(1)  # Simulate work

    progress_logger(5, total_steps, "Urban Cooling Model Completed!")
    print("All steps completed successfully.")

# Execute the model
execute_with_progress(args)
