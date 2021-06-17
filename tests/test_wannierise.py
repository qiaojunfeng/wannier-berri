"""Test the Data_K object."""

import numpy as np
import pytest
from pytest import approx

import wannierberri as wberri
from wannierberri.__Kpoint import KpointBZ
from wannierberri.__Data_K import Data_K

from create_system import create_files_Fe_W90, system_Fe_wberri_disentangle


def test_fourier(system_Fe_wberri_disentangle):
    """Compare slow FT and FFT."""
    system = system_Fe_wberi_disentangle
    return 1
