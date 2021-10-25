#!/usr/bin/env python3
from matplotlib import pyplot as plt
import numpy as np
from glob import glob

col = 1 
ndim = 2  # 0 for doc, 1 for ahc , 2 for a rank-2 tensor (e.g. berry dipole)
fig,ax=plt.subplots()
#for quant in "dos^1",:
#    for f in glob(f"Fe-{quant}_iter-??00.dat"):
for f in glob("chiral-berry_dipole^tetra*-NK=*_iter-0000.dat"):
        print (f)
        A=np.loadtxt(f)
        ax.plot(A[:,0],A[:,col],label=f'{f} Calculated')
#        ax.plot(A[:,0],A[:,col+3**ndim],'-',label=f'{f}Smoothed')
ax.set_xlabel('Efermi')
ax.legend()
plt.show()

