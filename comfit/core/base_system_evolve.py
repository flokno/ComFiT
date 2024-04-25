import numpy as np
import scipy as sp

class BaseSystemEvolve:
    ## Time evolution function
    def evolve_ETD2RK_loop(self, integrating_factors_f, nonlinear_evolution_function_f, field, field_f):
        """
        Evolves the given field using the ETD2RK scheme with a loop.

        Args:
            integrating_factors_f (list): A list of three integrating factors.
            nonlinear_evolution_function_f (function): A function that calculates the non-linear evolution of the field
                    and returns the fourier transform.
            field (ndarray): The initial field to be evolved.
            field_f (ndarray): The Fourier transform of the initial field.

        Output:
            tuple: A tuple containing the evolved field and the predicted field in Fourier space.
        """
        """
        Don't think this is needed. self.time is now initialized in base and all timedependence should be through this
        if t==None:
            def N_f(field,t):
                return nonlinear_evolution_function_f(field)
            t=0

        else:
            def N_f(field,t):
                return nonlinear_evolution_function_f(field,t)
        """
        N0_f = nonlinear_evolution_function_f(field, self.time)

        a_f = integrating_factors_f[0] * field_f + integrating_factors_f[1] * N0_f
        a = sp.fft.ifftn(a_f, axes=(range(-self.dim, 0)))

        N_a_f = nonlinear_evolution_function_f(a, self.time+self.dt)
        field_f = a_f + integrating_factors_f[2] * (N_a_f - N0_f)
        field = sp.fft.ifftn(field_f, axes=(range(-self.dim, 0)))

        self.time += self.dt

        return field, field_f

    def evolve_ETD4RK_loop(self, integrating_factors_f, nonlinear_evolution_function_f, field, field_f):

        """
         Evolves the given field using the ETD4RK scheme with a loop.

         Args:
             integrating_factors_f (list): A list of five integrating factors.
             nonlinear_evolution_function_f (function): A function that calculates the non-linear evolution of the field.
             field (ndarray): The initial field to be evolved.
             field_f (ndarray): The Fourier transform of the initial field.

         Output:
             tuple: A tuple containing the evolved field and the predicted field in Fourier space.
         """
        N_0f = nonlinear_evolution_function_f(field, self.time)

        a_f = field_f * integrating_factors_f[0] + N_0f * integrating_factors_f[1]
        a = sp.fft.ifftn(a_f, axes=(range(-self.dim, 0)))
        N_a = nonlinear_evolution_function_f(a, self.time + self.dt / 2)

        b_f = field_f * integrating_factors_f[0] + N_a * integrating_factors_f[1]
        b = sp.fft.ifftn(b_f, axes=(range(-self.dim, 0)))
        N_b = nonlinear_evolution_function_f(b, self.time + self.dt / 2)

        c_f = a_f * integrating_factors_f[0] + (2 * N_b - N_0f) * integrating_factors_f[1]
        c = sp.fft.ifftn(c_f, axes=(range(-self.dim, 0)))
        N_c = nonlinear_evolution_function_f(c, self.time + self.dt)

        field_f = field_f * integrating_factors_f[2] + N_0f * integrating_factors_f[3] \
                  + (N_a + N_b) * integrating_factors_f[4] + N_c * integrating_factors_f[5]

        field = sp.fft.ifftn(field_f, axes=(range(-self.dim, 0)))

        self.time += self.dt

        return field, field_f