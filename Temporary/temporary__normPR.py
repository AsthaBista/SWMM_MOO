# -*- coding: utf-8 -*-
"""
Created on Wed May  7 11:22:51 2025

@author: ABI
"""

PHI_base = base_results.loc[base_results['YEAR'] == year, 'PHI'].values[0]
PR_base = base_results.loc[base_results['YEAR'] == year, 'PR'].values[0]
TR_base = base_results.loc[base_results['YEAR'] == year, 'TR'].values[0]

norm_PHI = round(1 - (PHI / PHI_base),2) if PHI_base > 0 else 0
norm_PR = round(1 - (PR / PR_base),2) if PR_base > 0 else 0
norm_TR = round(1 - (TR / TR_base),2) if TR_base > 0 else 0
