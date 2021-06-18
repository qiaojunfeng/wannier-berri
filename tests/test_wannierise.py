"""Test the Data_K object."""

import numpy as np
import pytest
from pytest import approx

import wannierberri as wberri
from wannierberri.__Kpoint import KpointBZ
from wannierberri.__Data_K import Data_K

from create_system import create_files_Fe_W90, system_Fe_wberri_disentangle, aidata_Fe


def test_spread(system_Fe_wberri_disentangle):
    """Compare slow FT and FFT."""
    system = system_Fe_wberri_disentangle
    return 1

def test_energies(system_Fe_wberri_disentangle, aidata_Fe):
    """check if system reproduces the energies inside the frozen window"""
    system  = system_Fe_wberri_disentangle
    mp_grid = system.mp_grid
    grid = wberri.Grid(system, NKFFT=mp_grid, NKdiv=1)

    k=np.array([0.,0,0])
    dK = 1. / grid.div
    NKFFT = grid.FFT
    factor = 1./np.prod(grid.div)

    kpoint = KpointBZ(K=k, dK=dK, NKFFT=NKFFT, factor=factor, symgroup=None)

    assert kpoint.Kp_fullBZ == approx(k / grid.FFT)

    data  = Data_K(system, kpoint.Kp_fullBZ, grid=grid, Kpoint=kpoint, npar=0, fftlib='fftw')

    for ik_ai,kp in enumerate(aidata_Fe.kpt_mp_grid):
        ik = kp[2]+mp_grid[2]*(kp[1]+mp_grid[1]*kp[0])
        EK_wann = data.E_K[ik]
        EK_abi  = aidata_Fe.eig.data[ik_ai]
        frozen = ( EK_abi < aidata_Fe.froz_max) * ( EK_abi > aidata_Fe.froz_min)
        if np.any(frozen):
#            print (ik,ik_ai,kp,EK_abi,EK_wann,frozen,aidata_Fe.froz_min,aidata_Fe.froz_max)
            assert np.max(abs(EK_wann[frozen[:system.num_wann]]-EK_abi[frozen]))<1e-5, f"the interpolated bands {EK_wann} differ from the abinitio data {EK_abi} at point {ik_ai} ({ik})"

