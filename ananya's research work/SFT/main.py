"""
    Main script to generate a list of BMRs (bipolar magnetic regions) from HMI/SHARPs data.
    
    A.R Yeates, Durham University, updated Jul-2021
"""
import os
import datetime
import numpy as np
import matplotlib.pyplot as plt
import sharptools

#===========================================================
# SET INPUT PARAMETERS:

restart = True  # set to False if you want to regenerate all output

# Grid sizes in s=cos(theta) and phi:
ns = 181
nph = 361

# Required time range:
t_start = datetime.datetime(2014, 6, 10, 00)
t_end = datetime.datetime(2014, 12, 10, 00)

# Path to output directory [with trailing slash]:
outputpath = '/home/user/Desktop/test_folder/Phd_project/sharps_paper_test/'

# Parameters for emerging regions:
sharps_smoothing = 4
imbalance_threshold = 0.5
bmr_a = 0.56

# Parameters for removing repeat regions:
repeat_threshold = 1

# Method for selecting a single snapshot ('cm' or 'maxflux'):
method = 'cm'

# Type of magnetogram to use ('los' or 'br'):
magtype = 'br'

# Maximum distance east or west of central meridian to include [in degrees]:
maxlon = 90

if ((method=='maxflux') & (magtype=='los')):
    raise 'Error: incompatible options. It is not appropriate to select regions by maxflux and use line-of-sight magnetograms, because of errors near limb.'

#===========================================================

# Create output directory:
os.system('mkdir -p '+outputpath.replace(' ', '\ '))

# Query database and get pickle file outputput/sharps.p listing all SHARPs in interval:
sharptools.get_sharps(outputpath, t_start, t_end, restart, method=method, maxlon=maxlon)

# Read magnetograms for individual SHARPs and fit BMRs where possible:
sharptools.get_bmrs(outputpath, 'allsharps.txt', t_start, t_end, ns, nph, sharps_smoothing, imbalance_threshold, bmr_a, restart, plots=False, magtype=magtype, method=method, maxlon=maxlon)

# Determine repeated regions:
sharptools.get_pair_overlaps(outputpath, 'allsharps.txt', repeat_threshold=repeat_threshold, outfile='repeatpairs.txt', plots=False)

# Evolve SHARPs with BMRs forward in time and generate final database file:
sharptools.evolve_forward(outputpath, 'allsharps.txt', 'repeatpairs.txt', eta=350, v0=16e-3, p=2.33, outfile='bmrsharps_evol.txt', plots=False)
