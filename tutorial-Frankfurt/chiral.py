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
chiral=wb.models.Chiral(delta=2, t=1,hop2=1/3,phi=0,hopz=0.2)
# Call the interface for TBmodels to define the system class
syst=wb.System_PythTB(chiral,use_wcc_phase = True)
Efermi=np.linspace(-4,6,1000)
# Define some symmetries
syst.set_symmetry(['C3z',"TimeReversal"])
# After defining the symmetries, create the grid class
parallel=wb.Parallel(num_cpus=4)
# Define which quantities are going to be integrated
seedname="chiral"
num_iter=0


if False:
    for NK in 40,60,80,:
        grid=wb.Grid(syst,NK=(NK,NK,NK),NKFFT=(10,10,10))
        wb.integrate(syst,
            grid=grid,
            parallel=parallel,
            Efermi=Efermi,
            smearEf=100,
            quantities=["berry_dipole^tetra",
                        "berry_dipole",
                        "berry_dipole_fsurf^tetra",
                        "berry_dipole_fsurf",
                        "dos^tetra"],
            adpt_num_iter=num_iter,
            fout_name=seedname,
            suffix=f"NK={NK}",
            parameters = {"external_terms":False},
            specific_parameters = {"berry_dipole^tetra":{"tetra":True},
                                    "berry_dipole_fsurf^tetra":{"tetra":True} ,
                                    "dos^tetra":{"tetra":True} 
                                    },
            restart=False )


if False:
    wb.tabulate(syst,
            grid=grid,
            parallel=parallel,
            Efermi=Efermi,
            smearEf=300,
            quantities=["berry","Der_berry"],
            adpt_num_iter=num_iter,
            fout_name=seedname,
            restart=False )


if True:


    def ANC(data_K,Efermi,tetra=False,**parameters):
        return  wb.fermiocean.FermiOcean(
            wb.covariant_formulak.Omega(data_K,**parameters),
                data_K,Efermi,tetra,fder=1)()

#    from numba import njit
#    @njit
    def JDOS(data_K,Efermi,omega,smear=0.1):
        Energies_k=data_K.E_K
        jdos = np.zeros((len(Efermi),len(omega)))
        for ief,Ef in enumerate(Efermi):
            for E in Energies_k: # loop by k-point
                for e1 in E[E<=Ef]:  # occupied states
                    for e2 in E[E>Ef]:  # unoccupied states
                        jdos[ief]+=smear/((e2-e1-omega)**2+smear**2)
        return wb.__result.EnergyResult(
                [Efermi,omega], 
                jdos, 
                TRodd=False, Iodd=False, rank=0)
            

    import functools
    user_quantities = {
        'ahc_tetra' : functools.partial(wb.fermiocean.AHC, tetra=True,external_terms=False),
        'anomalous_Nernst' : ANC,
        'jdos':JDOS
        }

    for NK in 50,:
        grid=wb.Grid(syst,NK=(NK,NK,NK),NKFFT=(10,10,10))
        Efermi=np.linspace(-4,6,100)
        wb.integrate(syst,
            grid=grid,
            parallel=parallel,
            Efermi=Efermi,
            smearEf=100,
            user_quantities = user_quantities,
            adpt_num_iter=num_iter,
            fout_name=seedname,
            suffix=f"NK={NK}",
            parameters = {"external_terms":False},
            specific_parameters = {
                    "ahc_tetra":{"tetra":False},  # this has no effect 
                    "anomalous_Nernst":{"tetra":True,'external_terms':False},
                    "jdos" :{'omega':np.linspace(0,5,100),
                                'smear':0.5 }
                                },
            restart=False )


