import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import comfit as cf
import numpy as np
import matplotlib.pyplot as plt

bec = cf.BoseEinsteinCondensate(2,gamma=0.1)

bec.conf_initial_condition_Thomas_Fermi()

bec.conf_external_potential(0)

def V(t):
    radius = 20*bec.a0
    omega = 0.1
    position = (bec.xmid+radius*np.cos(omega*t), bec.ymid+radius*np.sin(omega*t))
    return bec.calc_Gaussian(position=position, top = 2, width=5*bec.a0)

bec.evolve_relax(100)
bec.conf_external_potential(V)

for n in range(200):
    bec.evolve_dGPE(50)
    bec.plot_complex_field(bec.psi)
    plt.draw()
    plt.pause(0.01)
    cf.tool_save_plot(n)
cf.tool_make_animation_gif(n)
