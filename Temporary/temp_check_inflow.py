# -*- coding: utf-8 -*-
"""
Created on Tue May 20 10:05:55 2025

@author: ABI
"""



import datetime
from swmm_api.input_file import SwmmInput

from pyswmm import Simulation, Nodes
import numpy as np


input_file = r"C:\Users\ABI\My_Files\MonteCarlo\SWMMFiles\Loren_singleblock_LT_perv_imperv_withouttrees.inp"
temp_inp = r"C:\Users\ABI\My_Files\MonteCarlo\SWMMFiles\model_temp.inp"
inp = SwmmInput(input_file)

for year in range(2021, 2023):
    sim_start = datetime.date(year, 5, 1)
    sim_end = datetime.date(year, 10, 31)
    inp.OPTIONS['START_DATE'] = sim_start
    inp.OPTIONS['END_DATE'] = sim_end
    inp.OPTIONS['REPORT_START_DATE'] = sim_start
    inp.write_file(temp_inp)
    
    inflows = []
    timestamps = []

    with Simulation(temp_inp) as sim:
        node = Nodes(sim)["O"]
        for step in sim:
            inflows.append(node.total_inflow)
            timestamps.append(sim.current_time)
           # print(node.total_inflow)
            
    sim_q = np.array(inflows)
    total_volume = round(sim_q.sum() * 60, 3)
    print(total_volume)