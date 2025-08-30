"""Module that contains classes to implement different reaction rates
"""

import numpy as np
import fipy as fp


class FirstOrderReaction(object):
    """Rate law for a simple first order reaction with constant rate coefficient

    .. math::
        rate(c) = k c
    """

    def __init__(self, k):
        """Initialize an object of :class:`first_order_reaction`.

        Args:
             k (float): Rate constant for the first order reaction
        """
        self._k = k

    def rate(self, concentration):
        """Calculate and return the reaction rate given a concentration value.

        Args:
            concentration (fipy.CellVariable): Concentration variable

        Returns:
             reaction_rate (fipy.ImplicitSourceTerm): Reaction rate
        """
        # return self._k * concentration
        return fp.ImplicitSourceTerm(coeff=self._k, var=concentration)


class LocalizedFirstOrderReaction(object):
    """Rate law for a first order reaction with spatially localized rate constant.

    The rate constant is a Gaussian function centered around the specified position with a specified width.

    .. math::
        rate(c) = k0 + k e^{-|\\vec{x}-\\vec{x}_0|^2/2\\sigma^2} c
    """

    def __init__(self, k0, k, sigma, x0, simulation_geometry):
        """Initialize an object of :class:`first_order_reaction`.

        Args:
             k0 (float): Basal rate constant uniform everywhere in space
             k (float): Amplitude of the Gaussian function for the first order reaction rate constant
             sigma (float): Width of the spatially varying Gaussian function
             x0 (float): Center of the spatially varying Gaussian function
             simulation_geometry (Geometry): Instance of one of the classes in :mod:`utils.geometry`
        """
        self._k0 = k0
        self._k = k
        self._sigma = sigma
        self._x0 = x0
        self._geometry = simulation_geometry
        self._rate_constant = self._k0 + self._k * np.exp(
            -self._geometry.get_mesh_distances_squared_from_point(reference_point=self._x0) / (2.0 * self._sigma ** 2))
        # self._rate_constant = (self._k0
        #                        + self._k
        #                        * (self._geometry.get_mesh_distances_squared_from_point(reference_point=self._x0) <
        #                           (2.0 * self._sigma)))

    def rate(self, concentration):
        """Calculate and return the reaction rate given a concentration value.

        Args:
            concentration (fipy.CellVariable): Concentration variable

        Returns:
             reaction_rate (fipy.ImplicitSourceTerm): Reaction rate
        """
        # return self._rate_constant * concentration
        return fp.ImplicitSourceTerm(coeff=self._rate_constant, var=concentration)

class LocalizedFirstOrderHillReaction(object):

    def __init__(self, k0, k, sigma, x0, hill_vmax, hill_c0, hill_kd, hill_n, hill_v0, simulation_geometry):
        self._k0 = k0
        self._k = k
        self._sigma = sigma
        self._x0 = x0
        self._geometry = simulation_geometry
        self._rate_constant = self._k0 + self._k * np.exp(
            -self._geometry.get_mesh_distances_squared_from_point(reference_point=self._x0) / (2.0 * self._sigma ** 2))
        self._hill_vmax  = hill_vmax
        self._hill_kd = hill_kd
        self._hill_c0 = hill_c0
        self._hill_n = hill_n
        self._hill_v0 = hill_v0
    def rate(self, concentration):
        """Calculate and return the reaction rate given a concentration value.

        Args:
            concentration (fipy.CellVariable): Concentration variable

        Returns:
             reaction_rate (fipy.ImplicitSourceTerm): Reaction rate
        """
        # return self._rate_constant * concentration
        hill_effect = self._hill_vmax * (concentration-self._hill_c0)**self._hill_n / ((concentration-self._hill_c0)**self._hill_n + self._hill_kd**self._hill_n) + self._hill_v0 
        return fp.ImplicitSourceTerm(coeff=self._rate_constant, var=hill_effect)

class LocalizedFirstOrderLinear(object):
    def __init__(self, k0, k, sigma, x0, linear_m, linear_c, simulation_geometry):
        self._k0 = k0
        self._k = k
        self._sigma = sigma
        self._x0 = x0
        self._geometry = simulation_geometry
        self._rate_constant = self._k0 + self._k * np.exp(
            -self._geometry.get_mesh_distances_squared_from_point(reference_point=self._x0) / (2.0 * self._sigma ** 2))
        self._linear_m  = linear_m
        self._linear_c = linear_c
    def rate(self, concentration):
        linear_effect = self._linear_m * concentration + self._linear_c
        return fp.ImplicitSourceTerm(coeff=self._rate_constant, var=linear_effect)