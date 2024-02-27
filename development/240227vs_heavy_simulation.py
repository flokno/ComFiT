import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import comfit as cf

pfc = cf.PhaseFieldCrystal3DBodyCenteredCubic(21,21,21)
eta = pfc.calc_amplitudes_with_dislocation_ring()
pfc.conf_PFC_from_amplitudes(eta)
pfc.evolve_PFC_hydrodynamic(100)