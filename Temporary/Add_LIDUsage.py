from swmm_api.input_file import SwmmInput
from swmm_api.input_file.sections.lid import LIDUsage


# Load the SWMM input file
input_file = r'C:\Users\ABI\OneDrive - NIVA\PhD_Work\Work\PartII\Loren\SWMM_MOO\SWMMFiles\Loren_singleblock_LT_temp_roofdisconnected.inp'
inp = SwmmInput(input_file)
modified_file = input_file.replace(".inp", "_modified.inp")

# Check if the LID_USAGE section exists, if not, create it
if "LID_USAGE" not in inp:
    inp["LID_USAGE"] = LIDUsage.create_section()
    
    


# Define LID parameters
subcatchment_name = "S5"
lid_name = "TRE"
lid_area = 39.0  
lid_width = 5
init_saturation = 0.0
from_impervious = 100.0  # 100% of runoff from impervious area goes to LID
to_pervious = 0.0
to_underdrain = 0.0  

# Assign the Green Roof LID to a subcatchment
new_lid_usage = LIDUsage(
    subcatchment=subcatchment_name,
    lid=lid_name,
    n_replicate=1,
    area=lid_area,
    width=lid_width ,
    saturation_init=init_saturation,
    impervious_portion=from_impervious,
    route_to_pervious=to_pervious,
    fn_lid_report='*',
    drain_to='*',
    from_pervious=0.0 
)


#inp.LID_USAGE.add_obj(new_lid_usage)
# # Add or update LID usage
inp["LID_USAGE"][(subcatchment_name, lid_name)] = new_lid_usage

# Save the modified SWMM input file (auto-formatted)

inp.write_file(modified_file)  # Automatically formats [LID_USAGE]