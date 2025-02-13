import pandas as pd
import os
from swmm_api import read_inp_file, SwmmInput
from pyswmm import Simulation
import matplotlib.pyplot as plt
import time
import openpyxl
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.optimize import minimize
import numpy as np
from pymoo.core.problem import ElementwiseProblem



# Combine paths safely
directory = r'C:\Users\ABI\OneDrive - NIVA\PhD_Work\Work\SWMM\Practice\Loren_T1'
file_name = 'Loren.inp'
full_path = os.path.join(directory, file_name)

# Starter tidtaking
start_time = time.time()

######################################################
######            2. INNGANGSVERDIER            ######
######################################################

infiltrasjonsrate = 50 # lokal infiltrasjonsrate [mm/t]

a_B1 = 1398        # areal i delfelt [m2]
a_B2 = 807       # areal i delfelt [m2]
a_B3 = 1385        # areal i delfelt [m2]
a_F1 = 802      # areal i delfelt [m2]
a_F2 = 840        # areal i delfelt [m2]


r_dis = 0.04       # diskonteringsrente
n_per = 50         # antall år

populasjon = 10   # populasjon for NSGA-ii
generasjoner = 5  # generasjoner for NSGA-ii

######################################################
#######       3. FOREBREDENDE BEREGNINGER       ######
######################################################

inp = read_inp_file(full_path)



# Setting up area in the subcatchemnts - Changing units from m2 to ha 
inp.SUBCATCHMENTS['B1'].area = a_B1/10000
inp.SUBCATCHMENTS['B2'].area = a_B2/10000
inp.SUBCATCHMENTS['B3'].area = a_B3/10000
inp.SUBCATCHMENTS['F1'].area = a_F1/10000
inp.SUBCATCHMENTS['F2'].area = a_F2/10000

# Setting the seepage in terrain LID as the infiltration rate
inp.LID_CONTROLS['PP'].layer_dict['STORAGE'].Seepage = infiltrasjonsrate

# Net present value factor - function of discount rate, and life span in years
NVF = ((1+r_dis)**n_per-1)/(r_dis*(1+r_dis)**n_per)     

# Cost of each LID - unit cost + variable cost factor x net present value ?? 
K_gr25 = 1500+20*NVF
K_pp =   2000+40*NVF
K_cfa =  1500+15*NVF #controlled flooded area
K_imp =  500+5*NVF

# Blue green factor
BGF_gr25 = 0.4
BGF_pp =   0.3
BGF_cfa =  1.0
BGF_imp =  0.2

inp.write_file('Loren_temp.inp')

# This converts the area in ha to m2 for easy calculations here
a_B1 = inp.SUBCATCHMENTS['B1'].area*10000
a_B2 = inp.SUBCATCHMENTS['B2'].area*10000
a_B3 = inp.SUBCATCHMENTS['B3'].area*10000


a_F1 = inp.SUBCATCHMENTS['F1'].area*10000
a_F2 = inp.SUBCATCHMENTS['F2'].area*10000

############################################################
########  4. DEFINERER FUNKSJON SOM SKAL OPTIMALISERES #####
############################################################

## Explanation of decision variables:
## For green roofs, total roof is taken, so the only variable is type of roof
## Here there are 3 roof catchments, so dv = 3
## For terrain subcatchments, there are two options here since we are 
## considering just one PP- to include or not. DV is the number of 
## terrain subcatchments : dv = 1, We also need the area allocated for each 
## terrain. So here dv becomes 2. Now total dv is 5.

class MyProblem(ElementwiseProblem):
    def __init__(self):
        super().__init__(n_var=7,                                   # antall variabler
                     n_obj=2,                                    # antall objektiver
                     n_ieq_constr=0,                             # begrensninger
                     xl=np.array([0,0,0,0,0]),     # nedre grense for variabler
                     xu=np.array([1,1,1,1,1]))     # øvre grense for variabler

    def _evaluate(self, x, out, *args, **kwargs):

        # Tilegner tiltaks-typer og tiltaks-areal til delfelt
    
        #############
        #### TAK ####
        #############
    
        #### B1 ####
        r1 = int(x[0] * 2) + 1
        if r1 == 1:
            inp.LID_USAGE[('B1', 'GR25')].area = a_B1
        else:
            inp.LID_USAGE[('B1', 'GR25')].area = 0
            
    
        #### B2 ####
        r2 = int(x[1] * 2) + 1
        if r2 == 1:
            inp.LID_USAGE[('B2', 'GR25')].area = a_B2
        else:
            inp.LID_USAGE[('B2', 'GR25')].area = 0
            
    
        #### B3 ####
        r3 = int(x[2] * 2) + 1
        if r3 == 1:
            inp.LID_USAGE[('B3', 'GR25')].area = a_B3
        else:
            inp.LID_USAGE[('B1', 'GR25')].area = 0
            
    
           
        #################
        #### TERRENG ####
        #################
    
        #### F1 ####
        r4 = int(x[3] * 2) + 1
        ra4 = x[4]
    
        if r4 == 1:
            inp.LID_USAGE[('F1', 'PP')].area = round(a_F1 * ra4, 0)
           
            inp.LID_USAGE[('F1', 'PP')].impervious_portion = 100
           
       
        else:
            inp.LID_USAGE[('F1', 'PP')].area = 0

            inp.LID_USAGE[('F1', 'PP')].impervious_portion = 0
    

        
    
    # Bestemmer nødvendig areal på kont.over.F5 gitt størrelse på LID-tiltak i andre felt
        for A in range(0, 1001, 10):
    def __init__(self):
        super().__init__(n_var=7,                                   # antall variabler
                         n_obj=2,                                    # antall objektiver
                         n_ieq_constr=0,                             # begrensninger
                         xl=np.array([0,0,0,0,0,0,0]),     # nedre grense for variabler
                         xu=np.array([1,1,1,1,1,1,1]))     # øvre grense for variabler

    def _evaluate(self, x, out, *args, **kwargs):

        # Tilegner tiltaks-typer og tiltaks-areal til delfelt

        #############
        #### TAK ####
        #############

        #### B1 ####
        r1 = int(x[0] * 2) + 1 
        # x(0) is between 0 to 1. 
        if r1 == 1:
            inp.LID_USAGE[('B1', 'GR25')].area = a_B1
            
        else:
            inp.LID_USAGE[('B1', 'GR25')].area = 0
           

        #### B2 ####
        r2 = int(x[1] * 2) + 1
        if r2 == 1:
           inp.LID_USAGE[('B2', 'GR25')].area = a_B2
           
        else:
           inp.LID_USAGE[('B2', 'GR25')].area = 0

        #### B3 ####
        r3 = int(x[2] * 2) + 1
        if r3 == 1:
           inp.LID_USAGE[('B3', 'GR25')].area = a_B3
           
        else:
           inp.LID_USAGE[('B3', 'GR25')].area = 0

               #################
        #### TERRENG ####
        #################

        #### F1 ####
        r4 = int(x[3] * 2) + 1
        ra4 = x[4]

        if r4 == 1:
            inp.LID_USAGE[('F1', 'PP')].area = round(a_F1 * ra4, 0)
            inp.LID_USAGE[('F1', 'PP')].impervious_portion = 100
          
        else:
            inp.LID_USAGE[('F1', 'PP')].area = 0
            inp.LID_USAGE[('F1', 'PP')].impervious_portion = 0

        #### F2 ####
        r5 = int(x[5] * 2) + 1
        ra5 = x[6]

        if r5 == 1:
             inp.LID_USAGE[('F2', 'PP')].area = round(a_F2 * ra5, 0)
             inp.LID_USAGE[('F2', 'PP')].impervious_portion = 100
           
        else:
             inp.LID_USAGE[('F2', 'PP')].area = 0
             inp.LID_USAGE[('F2', 'PP')].impervious_portion = 0

        

  # Determine the necessary area for flooding in F5, given the sizes of LID in other areas
        for A in range(0, 1001, 10):
            inp.STORAGE['St'].data[0] = A
            inp.write_file('Loren_temp.inp')
            with Simulation('Loren_temp.inp') as sim:
                for step in sim:
                    pass
            from swmm_api import read_rpt_file
            rpt = read_rpt_file('Loren_temp.rpt')  # type: swmm_api.SwmmReport
            node_inflow_summary = rpt.node_inflow_summary  # type: pandas.DataFrame
            Q_sim = node_inflow_summary.iloc[7, 2]
            if Q_sim < 6:
                print(inp.STORAGE['St'].data[0])
                break

        # Beregner kostnader og BGF
        area_gr25 = sum_area = sum(item.area for key, item in inp.LID_USAGE.items() if key[1] == 'GR25')
        
        area_tr = a_B1 + a_B2 + a_B3 - area_gr25             # tradisjonelt tak-areal

        
        area_pp = sum_area = sum(item.area for key, item in inp.LID_USAGE.items() if key[1] == 'PP')
        area_cfa = inp.STORAGE['St'].data[0]
        area_imp = a_F1 + a_F2 - area_pp - area_cfa
        area_tot = area_gr25 +area_tr + area_pp + area_cfa + area_imp

        # UTNYTTELSE = round((area_gr5 + area_gr20 + area_gr40 + area_gr80 + area_bc5 + area_bc15 + area_bc30 + area_pp + area_cfa) / area_tot,2)
        BGF = round((area_gr25 * BGF_gr25 + area_pp * BGF_pp  + area_cfa * BGF_cfa + area_imp * BGF_imp)/ area_tot,2)
               
          # Beregner kostnader og BGF
        area_gr5 = sum_area = sum(item.area for key, item in inp.LID_USAGE.items() if key[1] == 'GR5')
        area_gr20 = sum_area = sum(item.area for key, item in inp.LID_USAGE.items() if key[1] == 'GR20')
        area_gr40 = sum_area = sum(item.area for key, item in inp.LID_USAGE.items() if key[1] == 'GR40')
        area_gr80 = sum_area = sum(item.area for key, item in inp.LID_USAGE.items() if key[1] == 'GR80')
        area_tr = a_B1 + a_B2 + a_B3 + a_B4 - area_gr5 - area_gr20 - area_gr40 - area_gr80              # tradisjonelt tak-areal

        area_bc5 = sum_area = sum(item.area for key, item in inp.LID_USAGE.items() if key[1] == 'BC5')
        area_bc15 = sum_area = sum(item.area for key, item in inp.LID_USAGE.items() if key[1] == 'BC15')
        area_bc30 = sum_area = sum(item.area for key, item in inp.LID_USAGE.items() if key[1] == 'BC30')
        area_pp = sum_area = sum(item.area for key, item in inp.LID_USAGE.items() if key[1] == 'PP')
        area_cfa = inp.STORAGE['CFA'].data[0]
        area_imp = a_F1 + a_F2 + a_F3 + a_F4 + a_F5 - area_bc5 - area_bc15 - area_bc30 - area_pp - area_cfa
        area_tot = area_gr5 + area_gr20 + area_gr40 + area_gr80 + +area_tr + area_bc5 + area_bc15 + area_bc30 + area_pp + area_cfa + area_imp

        # UTNYTTELSE = round((area_gr5 + area_gr20 + area_gr40 + area_gr80 + area_bc5 + area_bc15 + area_bc30 + area_pp + area_cfa) / area_tot,2)
        BGF = round((
                area_gr5 * BGF_gr5
                + area_gr20 * BGF_gr20
                + area_gr40 * BGF_gr40
                + area_gr80 * BGF_gr80
                + area_tr * BGF_tr
                + area_bc5 * BGF_bc5
                + area_bc15 * BGF_bc15
                + area_bc30 * BGF_bc30
                + area_pp * BGF_pp
                + area_cfa * BGF_cfa
                + area_imp * BGF_imp
                    )/ area_tot,2)

        KOSTNAD = round( area_gr25 * K_gr25  + area_pp * K_pp + area_cfa * K_cfa + area_imp * K_imp,0)

        f1 = -BGF
        f2 = KOSTNAD+inp.STORAGE['St'].data[0]*10**-6        # Det er kostnad som er objektivet. Å legge til "inp.STORAGE['CFA'].data[0]*10**-6" er kun et triks for å bevare informasjon om areal på kontrollert oversvømmelsesareal (cfa) fra simuleringen.

        out["F"] = [f1, f2]

############################################################
########  5. HYPERPARAMETERE FOR NSGA-II ###################
############################################################


problem = MyProblem()

algorithm = NSGA2(
    pop_size=populasjon,
    eliminate_duplicates=True
)


res = minimize(problem,
                algorithm,
                ('n_gen',generasjoner),
                seed=1,
                save_history=True,
                verbose=True)

############################################################
########  6. SAMMENSTILLER OG PRESENTERER RESULTATER #######
############################################################


# omgjør BGF til positive verdier
res.F[res.F < 0] *= -1

# Lager en matrise for alle pareto-optimale løsninger

resF_df = pd.DataFrame(res.F, columns=['BGF', 'Kostnad [NOK]'])
resX_df = pd.DataFrame(res.X, columns=['x0', 'x1', 'x2', 'x3', 'x4'])

### Erstatningskart ###

kodekart_tak = {
    1: "GR25",
    2: "Ingen"
}

kodekart_ter = {
    1: "PP",
    2: "Ingen"
}

### B1 ###
resX_df['x0'] = resX_df['x0']*5
resX_df['x0'] = resX_df['x0'].astype(int)+1
resX_df['x0'] = resX_df['x0'].replace(kodekart_tak)
resX_df = resX_df.rename(columns={'x0': 'B1 type tiltak'})

### B2 ###
resX_df['x1'] = resX_df['x1']*5
resX_df['x1'] = resX_df['x1'].astype(int)+1
resX_df['x1'] = resX_df['x1'].replace(kodekart_tak)
resX_df = resX_df.rename(columns={'x1': 'B2 type tiltak'})

### B3 ###
resX_df['x2'] = resX_df['x2']*5
resX_df['x2'] = resX_df['x2'].astype(int)+1
resX_df['x2'] = resX_df['x2'].replace(kodekart_tak)
resX_df = resX_df.rename(columns={'x2': 'B3 type tiltak'})

### B4 ###
resX_df['x3'] = resX_df['x3']*5
resX_df['x3'] = resX_df['x3'].astype(int)+1
resX_df['x3'] = resX_df['x3'].replace(kodekart_tak)
resX_df = resX_df.rename(columns={'x3': 'B4 type tiltak'})

### F1 ###
resX_df['x4'] = resX_df['x4']*5
resX_df['x4'] = resX_df['x4'].astype(int)+1
resX_df['x4'] = resX_df['x4'].replace(kodekart_ter)
resX_df = resX_df.rename(columns={'x4': 'F1 type tiltak'})

resX_df['x5'] = round(resX_df['x5']*a_F1,0)
resX_df = resX_df.rename(columns={'x5': 'F1 areal tiltak'})
resX_df.loc[resX_df['F1 type tiltak'] == "Ingen", 'F1 areal tiltak'] = 0

### F2 ###
resX_df['x6'] = resX_df['x6']*5
resX_df['x6'] = resX_df['x6'].astype(int)+1
resX_df['x6'] = resX_df['x6'].replace(kodekart_ter)
resX_df = resX_df.rename(columns={'x6': 'F2 type tiltak'})

resX_df['x7'] = round(resX_df['x7']*a_F2,0)
resX_df = resX_df.rename(columns={'x7': 'F2 areal tiltak'})
resX_df.loc[resX_df['F2 type tiltak'] == "Ingen", 'F2 areal tiltak'] = 0

### F3 ###
resX_df['x8'] = resX_df['x8']*5
resX_df['x8'] = resX_df['x8'].astype(int)+1
resX_df['x8'] = resX_df['x8'].replace(kodekart_ter)
resX_df = resX_df.rename(columns={'x8': 'F3 type tiltak'})

resX_df['x9'] = round(resX_df['x9']*a_F3,0)
resX_df = resX_df.rename(columns={'x9': 'F3 areal tiltak'})
resX_df.loc[resX_df['F3 type tiltak'] == "Ingen", 'F3 areal tiltak'] = 0

### F4 ###
resX_df['x10'] = resX_df['x10']*5
resX_df['x10'] = resX_df['x10'].astype(int)+1
resX_df['x10'] = resX_df['x10'].replace(kodekart_ter)
resX_df = resX_df.rename(columns={'x10': 'F4 type tiltak'})

resX_df['x11'] = round(resX_df['x11']*a_F4,0)
resX_df = resX_df.rename(columns={'x11': 'F4 areal tiltak'})
resX_df.loc[resX_df['F4 type tiltak'] == "Ingen", 'F4 areal tiltak'] = 0



### SAMLER RESULTATER ###
res_df = pd.concat([resF_df, resX_df], axis=1)

res_df['F5 type tiltak'] = "CFA"
res_df['F5 areal tiltak'] = round(10**6*(res_df['Kostnad [NOK]']-round(res_df['Kostnad [NOK]'],0)),0)
res_df['Kostnad [NOK]'] = round(res_df['Kostnad [NOK]'],0)

print(res_df)
res_df.to_excel('Pareto optimal solutions.xlsx', index=False)


x_data = res_df['BGF']
y_data = res_df['Kostnad [NOK]']

# Lag et scatterplot
plt.scatter(x_data, y_data)


# Legg til aksetitler
plt.xlabel('BGF')
plt.ylabel('Kostnad [NOK]')

# Vis plottet
plt.show()


end_time = time.time()
elapsed_time = round(end_time - start_time,0)
print(f"Tid brukt på beregninger: {elapsed_time} sekunder")
