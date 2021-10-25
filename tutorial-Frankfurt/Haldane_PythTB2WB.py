#!/usr/bin/env python3
import os
os.environ['OPENBLAS_NUM_THREADS'] = '1' 
os.environ['MKL_NUM_THREADS'] = '1'
import matplotlib
matplotlib.use('Agg')
import wannierberri as wb
SYM=wb.symmetry
import numpy as np

# Define the model for a fixed set of parameters
haldane=wb.models.Haldane_ptb(delta=2, t=1,t2=1/3,phi=np.pi/10)
# Call the interface for TBmodels to define the system class
syst=wb.System_PythTB(haldane)
Efermi=np.linspace(-4,6,1000)
# Define some symmetries
syst.set_symmetry(['C3z'])
# After defining the symmetries, create the grid class
grid=wb.Grid(syst,NK=(200,200,1),NKFFT=(20,20,1))
parallel=wb.Parallel(num_cpus=8)
# Define which quantities are going to be integrated
seedname="pythtb_Haldane"
num_iter=10


wb.integrate(syst,
            grid=grid,
            parallel=parallel,
            Efermi=Efermi,
            smearEf=300,
            quantities=["berry_dipole^tetra",
                        "berry_dipole",
                        "berry_dipole_fsurf^tetra",
                        "berry_dipole"],
            adpt_num_iter=num_iter,
            fout_name=seedname,
            parameters = {"external_terms":False},
            specific_parameters = {"berry_dipole^tetra":{"tetra":True},
                                    "berry_dipole^tetra":{"tetra":True} },
            restart=False )


if False:
    wb.tabulate(syst,
            grid=grid,
            parallel=parallel,
            Efermi=Efermi,
            smearEf=300,
            quantities=q_int,
            adpt_num_iter=num_iter,
            fout_name=seedname,
            restart=False )

