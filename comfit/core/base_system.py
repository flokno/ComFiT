import numpy as np
import matplotlib.pyplot as plt
from comfit.tools.tool_colormaps import tool_colormap_angle, tool_colormap_bluewhitered
from mpl_toolkits.mplot3d import Axes3D  # for 3D plotting
from skimage.measure import marching_cubes
from matplotlib.tri import Triangulation



class BaseSystem:
    def __init__(self, dimension, xRes=101, dx=1.0, yRes=101, dy=1.0, zRes=101, dz=1.0, dt=0.1, **kwargs):
        self.dim = dimension
        self.xRes = xRes
        self.yRes = 1
        self.zRes = 1

        if dimension > 1:
            self.yRes = yRes

        if dimension > 2:
            self.zRes = zRes

        self.dx = dx
        self.dy = dy
        self.dz = dz
        self.dt = dt

        if self.dim not in [1, 2, 3]:
            raise ValueError('Dimension must be 1, 2, or 3.')

        self.x = np.arange(0, self.xRes * self.dx, self.dx)
        self.y = np.array([0])
        self.z = np.array([0])

        if self.dim > 1:
            self.y = np.arange(0, self.yRes * self.dy, self.dy)
        if self.dim > 2:
            self.z = np.arange(0, self.zRes * self.dz, self.dz)

        self.Res = self.xRes * self.yRes * self.zRes
        self.dims = [self.yRes, self.xRes, self.zRes]

        self.a0 = 1  # System length PFCscale, set to 1 unless changed later

        # Helpful midpoints and their indices
        self.xmidi = (1 + self.xRes) // 2 - 1
        self.xmid = self.x[self.xmidi]

        self.ymidi = (1 + self.yRes) // 2 - 1
        self.ymid = self.y[self.ymidi]

        self.zmidi = (1 + self.zRes) // 2 - 1
        self.zmid = self.z[self.zmidi]

        self.midi = self.xRes * self.yRes * (self.zmidi - 1) + self.yRes * (self.xmidi - 1) + self.ymidi
        self.rmid = [self.xmid, self.ymid, self.zmid]

        # Max positions
        self.xmax = self.x[-1] + self.dx
        self.ymax = self.y[-1] + self.dy if self.dim > 1 else 0
        self.zmax = self.z[-1] + self.dz if self.dim > 2 else 0

        # Fourier modes
        self.k = [self.calc_wavenums(self.x)]
        if self.dim == 2:
            self.k[0] = self.k[0].reshape(self.xRes, 1)
            self.k.append(self.calc_wavenums(self.y).reshape(1, self.yRes))
        elif self.dim == 3:
            self.k[0] = self.k[0].reshape(self.xRes, 1, 1)
            self.k.append(self.calc_wavenums(self.y).reshape(1, self.yRes, 1))
            self.k.append(self.calc_wavenums(self.z).reshape(1, 1, self.zRes))

        # Derivatives
        self.dif = [1j * ki for ki in self.k]

        self.dV = self.dx
        if self.dim > 1:
            self.dV *= self.dy
        if self.dim > 2:
            self.dV *= self.dz

        self.xmin = 0
        self.ymin = 0
        self.zmin = 0

        self.rmin = [self.xmin, self.ymin, self.zmin]
        self.rmax = [self.xmax, self.ymax, self.zmax]

    # Calculation of angle fields for vortices of different types
    def calc_angle_field_single_vortex(self,
                                       position=None,
                                       charge=1):
        if self.dim != 2:
            raise Exception("The dimension of the system must be 2 for a single point vortex.")

        if position is None:
            position = [self.xmid, self.ymid]

        x = self.x.reshape((self.xRes, 1))
        y = self.y.reshape((1, self.yRes))

        theta = charge * np.arctan2(y - position[1], x - position[0])

        return theta

    def calc_angle_field_double_vortex(self,
                                       position1=None,
                                       position2=None):

        if self.dim != 2:
            raise Exception("The dimension of the system must be 2 for a single point vortex.")

        if position1 is None:
            position1 = [self.xmax / 3, self.ymid]

        if position2 is None:
            position2 = [2 * self.xmax / 3, self.ymid]

        theta1 = self.calc_angle_field_single_vortex(position1)
        theta2 = self.calc_angle_field_single_vortex(position2, charge=-1)

        return np.mod(theta1 + theta2 + np.pi, 2 * np.pi) - np.pi

    def calc_wavenums(self, x):
        """
        Calculates the wavenumbers corresponding to the input position vectors given by x.

        Parameters:
        - x : numpy array
            1D array of x-positions.

        Returns:
        - k : numpy array
            1D array of wavenumbers with all the modes for the given x-array,
            assuming periodicity from x[0] to x[0] over n intervals.

        Example:
        x = np.array([-10, -5, 0, 5, 10])
        k = instance_of_BaseSystem.calc_wavenums(self,x)
        print(k)
        # Output: [ 0.          0.25132741  0.50265482 -0.50265482 -0.25132741]
        """
        n = len(x)

        high = (n - 1) // 2
        low = - (n // 2)

        l = n * (x[1] - x[0])

        k = np.concatenate((np.arange(0, high + 1), np.arange(low, 0))) * 2 * np.pi / l

        return k

    def calc_k2(self):
        return sum([self.k[i] ** 2 for i in range(len(self.k))])

    def calc_defect_field(self, psi, psi0=1):

        if self.dim == 2:
            if len(psi) == 2:
                psi_f = [np.fft.fftn(psi[0]), np.fft.fftn(psi[1])]

                return 1 / (np.pi * psi0 ** 2) * np.real(
                    np.fft.ifftn(self.dif[0] * psi_f[0]) * np.fft.ifftn(self.dif[1] * psi_f[1]) -
                    np.fft.ifftn(self.dif[1] * psi_f[0]) * np.fft.ifftn(self.dif[0] * psi_f[1]))

    def calc_defect_field_singular(self,psi0=1):
        return calc_defect_density(self,psi,1)*calc_delta_function(psi,psi0)

    def calc_delta_function(self,psi,psi0=1):
        width = psi0 / 10
        n = len(psi)
        if self.dim == 2:
            if n == 2:
                psi2 = psi[0]**2 + psi[1]**2
                return 1/(2*np.pi*width**2)*np.exp(-psi2/(2*width**2))


    # plotting functions
    def plot_angle_field(self, field):
        X, Y = np.meshgrid(self.x, self.y, indexing='ij')

        custom_colormap = tool_colormap_angle()

        mesh = plt.pcolormesh(X, Y, field, shading='auto', cmap=custom_colormap)
        cbar = plt.colorbar(mesh)  # To add a colorbar on the side
        cbar.set_ticks(np.array([-np.pi, -2 * np.pi / 3, -np.pi / 3, 0, np.pi / 3, 2 * np.pi / 3, np.pi]))
        cbar.set_ticklabels([r'$-\pi$', r'$-2\pi/3$', r'$-\pi/3$', r'$0$', r'$\pi/3$', r'$2\pi/3$', r'$\pi$'])
        plt.title("Angle field")
        plt.xlabel("X-axis")
        plt.ylabel("Y-axis")

    def plot_field(self, field, ax=None, colorbar=True, colormap='viridis', cmax=None, cmin=None,
                   number_of_layers=1,hold=False):



        if self.dim == 1:

            ax.plot(self.x, field)


        elif self.dim == 2:
            if ax == None:
                ax = plt.gcf().add_subplot(111)

            X, Y = np.meshgrid(self.x, self.y, indexing='ij')

            pcm = ax.pcolormesh(X / self.a0, Y / self.a0, field, shading='gouraud', cmap=colormap)
            ax.set_aspect('equal')

            if cmin is not None:
                pcm.set_clim(vmin=cmin)
            if cmax is not None:
                pcm.set_clim(vmax=cmax)

            if colorbar:
                cbar = plt.colorbar(pcm, ax=ax)

            if hasattr(self, 'defined_length_scale'):
                ax.set_xlabel('$x/a_0$')
                ax.set_ylabel('$y/a_0$')
            else:
                ax.set_xlabel('$x$')
                ax.set_ylabel('$y$')

            return ax

        elif self.dim == 3:

            if ax == None:
                plt.figure()
                ax = plt.gcf().add_subplot(111, projection='3d')

            if not hold:
                ax.clear()

            X, Y, Z = np.meshgrid(self.x, self.y, self.z, indexing='ij')

            field_min = np.min(field)
            field_max = np.max(field)

            layer_values = np.linspace(field_min, field_max, number_of_layers + 2)
            print(layer_values)

            cmap = plt.get_cmap('viridis')

            verts, faces, _, _ = marching_cubes(field, layer_values[1])

            ax.plot_trisurf(verts[:, 0], verts[:, 1], faces, verts[:, 2],alpha=0.5,color=cmap(layer_values[1]/field_max))

            for layer_value in layer_values[2:-1]:
                print(layer_value)
                verts, faces, _, _ = marching_cubes(field, layer_value)
                ax.plot_trisurf(verts[:, 0], verts[:, 1], faces, verts[:, 2],alpha=0.5,color=cmap(layer_value/field_max))

            ax.set_aspect('equal')
            if colorbar:
                sm = plt.cm.ScalarMappable(cmap=cmap)
                sm.set_clim(field_min, field_max)
                plt.colorbar(sm, ax=ax)

            return ax

    def plot_fourier_field(self, field_f, ax=None):
        field_f = np.fft.fftshift(field_f)

        if ax == None:
            ax = plt.gcf().add_subplot(111, projection='3d')

        if self.dim == 2:
            rho = np.abs(field_f)
            theta = np.angle(field_f)

            Kx, Ky = np.meshgrid(self.k[0], self.k[1], indexing='ij')

            Kx = np.fft.fftshift(Kx)
            Ky = np.fft.fftshift(Ky)

            custom_colormap = tool_colormap_angle()

            # Get the colors from a colormap (e.g., hsv, but you can choose any other)
            colors = plt.cm.hsv((theta + np.pi) / (2 * np.pi))  # Normalizing theta to [0, 1]
            ic(theta)
            surf = ax.plot_surface(Kx, Ky, rho, facecolors=colors, shade=True)

            # mappable = plt.cm.ScalarMappable(cmap=custom_colormap)
            # mappable.set_array([])
            # mappable.set_clim(-np.pi, np.pi)
            # cbar = plt.colorbar(mappable, ax=ax)
            # cbar.set_ticks(np.array([-np.pi, -2 * np.pi / 3, -np.pi / 3, 0, np.pi / 3, 2 * np.pi / 3, np.pi]))
            # cbar.set_ticklabels([r'$-\pi$', r'$-2\pi/3$', r'$-\pi/3$', r'$0$', r'$\pi/3$', r'$2\pi/3$', r'$\pi$'])

            # plt.title("Angle field")
            # plt.xlabel("X-axis")
            # plt.ylabel("Y-axis")

    def plot_complex_field(self, complex_field, ax=None):

        if ax == None:
            ax = plt.gcf().add_subplot(111, projection='3d')

        if self.dim == 2:
            rho = np.abs(complex_field)
            theta = np.angle(complex_field)

            X, Y = np.meshgrid(self.x, self.y, indexing='ij')

            custom_colormap = tool_colormap_angle()

            # Get the colors from a colormap (e.g., hsv, but you can choose any other)
            colors = plt.cm.hsv((theta + np.pi) / (2 * np.pi))  # Normalizing theta to [0, 1]

            surf = ax.plot_surface(X, Y, rho, facecolors=colors)

            # mappable = plt.cm.ScalarMappable(cmap=custom_colormap)
            # mappable.set_array([])
            # mappable.set_clim(-np.pi, np.pi)
            # cbar = plt.colorbar(mappable, ax=ax)
            # cbar.set_ticks(np.array([-np.pi, -2 * np.pi / 3, -np.pi / 3, 0, np.pi / 3, 2 * np.pi / 3, np.pi]))
            # cbar.set_ticklabels([r'$-\pi$', r'$-2\pi/3$', r'$-\pi/3$', r'$0$', r'$\pi/3$', r'$2\pi/3$', r'$\pi$'])

            # plt.title("Angle field")
            # plt.xlabel("X-axis")
            # plt.ylabel("Y-axis")



        else:
            raise Exception("This plotting function not yet configured for other dimension")

    # Time evolution function
    def evolve_ETDRK2_loop(self, integrating_factors_f, non_linear_evolution_function_f, field, field_f,
                           number_of_pred_it_steps=2):

        N0_f = non_linear_evolution_function_f(field)
        # This needs to be generalized

        for i in range(number_of_pred_it_steps):
            if i == 1:
                dN_f = 0
            else:
                dN_f = non_linear_evolution_function_f(field) - N0_f

            # print(N0_f)
            field_f_pred = integrating_factors_f[0] * field_f + \
                           integrating_factors_f[1] * N0_f + \
                           integrating_factors_f[2] * dN_f

            # TODO: simplify this piece of code (Vidar 08.09.23)

            if self.dim == 1:
                field_f_pred[0] = field_f[0]
            elif self.dim == 2:
                field_f_pred[0, 0] = field_f[0, 0]
            elif self.dim == 3:
                field_f_pred[0, 0, 0] = field_f[0, 0, 0]

            field = np.fft.ifftn(field_f_pred,axes =(range(-self.dim,0)))

        return field, field_f_pred
