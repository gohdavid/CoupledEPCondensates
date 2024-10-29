"""Module that contains classes describing different free energies.
"""

import numpy as np
import fipy as fp


class TwoCompDoubleWellFHCrossQuadratic(object):
    """Free energy of two component system with a quartic well and quadratic well self, and FH cross interactions.

    This class describes the free energy density of a two component system given by the below expression:

    .. math::

       f[c_1, c_2, \\vec{r}] = f_{bulk}[c_1, c_2] + f_{BL}[c_1, \\vec{r}] =
       = 0.25 \\alpha (c_1-\\bar{c}_1)^4 + 0.5 \\beta (c_1-\\bar{c}_1)^2 + \\gamma c_1 c_2
       + 0.5 \\lambda c^2_2 + 0.5 \\kappa |\\nabla c_1|^2
       - c \\exp^{-|\\vec{r}-\\vec{r}_0|^2/2\\sigma^2} c_1

    Interactions between molecules of species 1 are described by a quartic-well potential. If :math:`\\beta < 0`, then
    we get a double-well and species 1 can phase separate by itself.

    Interactions between molecules of species 2 are described by a quadratic potential. For this term, :math:`\\lambda`
    has to be > 0. Otherwise, the self diffusion of species 2 will cause all molecules to collapse into a point.

    The cross interactions between the species are described by a mean-field product of concentrations with the
    interaction strength captured by a Flory parameter :math:`\\gamma`
    """

    def __init__(self, alpha, beta, gamma, lamda, kappa, c_bar_1, well_center, well_depth, sigma):
        """Initialize an object of :class:`TwoCompDoubleWellFHCrossQuadratic`.

        Args:
            alpha (float): Parameter associated with the quartic term :math:`\\alpha (c_1-\\bar{c}_1)^4` of species 1

            beta (float): Parameter associated with the quadratic term :math:`\\beta (c_1-\\bar{c}_1)^2` of species 1

            gamma (float): Parameter that describes the cross-interactions between the species :math:`\\gamma c_1 c_2`

            lamda (float): Parameter that describes the self interaction of species 2 using :math:`\\lambda c^2_2`

            kappa (float): Parameter that describes the surface tension associated with species 1
            :math:`\\kappa/2 |\\nabla c_1|^2`

            c_bar_1 (float): Critical concentration of species 1 at the onset of phase separation

            well_center (numpy.ndarray): Coordinates of the center of a Gaussian attractive well. 2d or 3D array

            well_depth (float): Depth of the Gaussian well

            sigma (float): Width of the Gaussian well
        """

        self._free_energy_type = 1

        # Ensure that the parameter lambda is always positive
        # Otherwise, we will get nonsense results in the simulations
        assert lamda > 0, "The parameter lambda is negative. Please supply a positive value"

        # Assign all free energy parameters to private variables
        self._alpha = alpha
        self._beta = beta
        self._gamma = gamma
        self._lambda = lamda
        self._kappa = kappa
        self._c_bar_1 = c_bar_1
        self._well_center = well_center
        self._well_depth = well_depth
        self._sigma = sigma

    @property
    def kappa(self):
        """Getter for the private variable self._kappa.
        This is used to set up the surface tension term in the dynamical equations"""
        return self._kappa

    def get_gaussian_function(self, mesh):
        """Function that calculates :math:`e^{-|\\vec{r}-\\vec{r}_0|^2/2\\sigma^2}`

        Args:
            mesh (fipy or Gmsh mesh): A mesh generated by fipy in-built functions or Gmsh

        Returns:
            gaussian_function (fipy.cellVariable): A variable storing the Gaussian function evaluated at each mesh point
        """
        # Get mesh dimensions from the CellVariables in c_vector
        mesh_dimensions = np.shape(mesh.cellCenters.value)[0]
        # Calculate distance of each mesh point from the center of the Gaussian well
        distance_squared_from_well_center = np.sum([(mesh.cellCenters[i] - self._well_center[i]) ** 2
                                                    for i in range(mesh_dimensions)], 0)
        gaussian_function = fp.CellVariable(mesh=mesh,
                                            value=np.exp(-distance_squared_from_well_center / (2 * self._sigma ** 2)))
        gaussian_function = self._well_depth * gaussian_function
        return gaussian_function

    def calculate_fe(self, c_vector):
        """Calculate free energy according to the expression in class description.

        Args:
            c_vector (numpy.ndarray): A 2x1 vector of species concentrations that looks like :math:`[c_1, c_2]`.
            The concentration variables :math:`c_1` and :math:`c_2` must be instances of the class
            :class:`fipy.CellVariable` or equivalent. These instances should have an attribute called :attr:`.grad.mag`
            that returns the magnitude of gradient of the concentration field for every position in the mesh to compute
            the surface tension contribution of the free energy

        Returns:
            free_energy (fipy.cellVariable): Free energy value
        """

        # Check that c_vector satisfies the necessary conditions
        assert len(c_vector) == 2, \
            "The shape of c_vector passed to TwoCompDoubleWellFHCrossQuadratic.calculate_fe() is not 2x1"
        assert hasattr(c_vector[0], "grad"), \
            "The instance c_vector[0] has no attribute grad associated with it"
        assert hasattr(c_vector[1], "grad"), \
            "The instance c_vector[1] has no function grad associated with it"
        assert hasattr(c_vector[0].grad, 'mag'), \
            "The instance c_vector[0].grad has no attribute mag associated with it"
        assert hasattr(c_vector[1].grad, 'mag'), \
            "The instance c_vector[1].grad has no attribute mag associated with it"

        # Calculate the free energy
        fe = (self._alpha / 4.0 * (c_vector[0] - self._c_bar_1) ** 4
              + self._beta / 2.0 * (c_vector[0] - self._c_bar_1) ** 2
              - self.get_gaussian_function(c_vector[0].mesh) * c_vector[0]
              + self._gamma * c_vector[0] * c_vector[1]
              + self._lambda * c_vector[1] ** 2
              + 0.5 * self._kappa * c_vector[0].grad.mag ** 2)

        return fe

    def calculate_mu(self, c_vector):
        """Calculate chemical potential of the species.

        Chemical potential of species 1:

        .. math::

            \\mu_1[c_1, c_2] = \\delta f / \\delta c_1 = \\alpha (c_1-\\bar{c}_1)^3 + \\beta (c_1-\\bar{c}_1)
                               + \\gamma c_2 - \\kappa \\nabla^2 c_1 - K \\exp^{-|\\vec{r}-\\vec{r}|^2/2\\sigma^2}

        Chemical potential of species 2:

        .. math::

            \\mu_2[c_1, c_2] = \\delta f / \\delta c_2 = \\gamma c_1 + \\lambda c_2


        Args:
            c_vector (numpy.ndarray): A 2x1 vector of species concentrations that looks like :math:`[c_1, c_2]`. The
            concentration variables :math:`c_1` and :math:`c_2` must be instances of the class
            :class:`fipy.CellVariable` or equivalent. These instances should have an attribute called
            :attr:`.faceGrad.divergence` that returns the Laplacian of the concentration field for every position in the
            mesh to compute the surface tension contribution to the chemical potential of species 1

        Returns:
            mu (list): A 2x1 vector of chemical potentials that looks like :math:`[\\mu_1, \\mu_2]`
        """

        # Check that c_vector satisfies the necessary conditions
        assert len(c_vector) == 2, \
            "The shape of c_vector passed to TwoCompDoubleWellFHCrossQuadratic.calculate_mu() is not 2x1"
        assert hasattr(c_vector[0], "faceGrad"), \
            "The instance c_vector[0] has no attribute faceGrad associated with it"
        assert hasattr(c_vector[1], "faceGrad"), \
            "The instance c_vector[1] has no attribute faceGrad associated with it"
        assert hasattr(c_vector[0].faceGrad, "divergence"), \
            "The instance c_vector[0].faceGrad has no attribute divergence associated with it"
        assert hasattr(c_vector[1].faceGrad, "divergence"), \
            "The instance c_vector[1].faceGrad has no attribute divergence associated with it"

        # Calculate the chemical potentials
        mu_1 = (self._alpha * (c_vector[0] - self._c_bar_1) ** 3
                + self._beta * (c_vector[0] - self._c_bar_1)
                - self.get_gaussian_function(c_vector[0].mesh)
                + self._gamma * c_vector[1]
                - self._kappa * c_vector[0].faceGrad.divergence)
        mu_2 = self._gamma * c_vector[0] + self._lambda * c_vector[1]
        mu = [mu_1, mu_2]

        return mu

    def calculate_jacobian(self, c_vector):
        """Calculate the Jacobian matrix of coefficients to feed to the transport equations.

        In calculating the Jacobian, we ignore the surface tension and any spatially dependent terms and only take the
        bulk part of the free energy that depends on the concentration fields:

        .. math::
            J_{11} = \\delta^2 f_{bulk} / \\delta c^2_1 = 3 \\alpha (c_1 - \\bar{c}_1)^2 + \\beta

        .. math::
            J_{12} = \\delta^2 f_{bulk} / \\delta c_1 \\delta c_2 = \\gamma

        .. math::
            J_{21} = \\delta^2 f_{bulk} / \\delta c_1 \\delta c_2 = \\gamma

        .. math::
            J_{22} = \\delta^2 f_{bulk} / \\delta c^2_2 = \\lambda

        Args:
            c_vector (numpy.ndarray): A 2x1 vector of species concentrations that looks like :math:`[c_1, c_2]`.The
            concentration variables :math:`c_1` and :math:`c_2` must be instances of the class
            :class:`fipy.CellVariable` or equivalent
        Returns:
            jacobian (numpy.ndarray): A 2x2 Jacobian matrix, with each entry itself being a vector of the same size as
            c_vector[0]
        """

        # Check that c_vector satisfies the necessary conditions
        assert len(c_vector) == 2, \
            "The shape of c_vector passed to TwoCompDoubleWellFHCrossQuadratic.calculate_mu() is not 2x1"

        # Calculate the Jacobian matrix
        jacobian = np.array([[3 * self._alpha * (c_vector[0] - self._c_bar_1) ** 2 + self._beta, self._gamma],
                             [self._gamma, self._lambda]])
        return jacobian


class TwoCompDoubleWellFHCrossQuadraticDimensionless(object):
    """Dimensionless free energy of two component system with a double well self, and FH cross interactions.

    This class describes the free energy density of a two component system given by the below expression:

    .. math::

       \\tilde{f}[\\tilde{c}_1, \\tilde{c}_2, \\vec{r}] =
       \\tilde{f}_{bulk}[\\tilde{c}_1, \\tilde{c}_2] + \\tilde{f}_{BL}[\\tilde{c}_1, \\vec{r}] =
       0.25 (\\tilde{c}_1-\\bar{c_1})^4 + 0.5 \\tilde{\\beta} (\\tilde{c}_1-\\bar{c_1})^2
       + \\tilde{\\gamma} \\tilde{c}_1 \\tilde{c}_2 + 0.5 \\tilde{\\lambda} \\tilde{c}^2_2
       + 0.5 \\tilde{\\kappa} |\\tilde{\\nabla} \\tilde{c}_1|^2
       - \\tilde{c} e^{-|\\vec{r}-\\vec{r}_0|^2/2\\sigma^2} \\tilde{c}_1

    Interactions between molecules of species 1 are described by a quartic-well potential. If
    :math:`\\tilde{\\beta} < 0`, then we get a double-well and species 1 can phase separate by itself.

    Interactions between molecules of species 2 are described by a quadratic potential. For this term,
    :math:`\\tilde{\\lambda}` has to be > 0. Otherwise, the self diffusion of species 2 will cause all molecules to
    collapse into a point.

    The cross interactions between the species are described by a mean-field product of concentrations with the
    interaction strength captured by a Flory parameter :math:`\\tilde{\\gamma}`
    """

    def __init__(self, c_bar_1, beta_tilde, gamma_tilde, lamda_tilde, kappa_tilde, well_center, well_depth, sigma):
        """Initialize an object of :class:`TwoCompDoubleWellFHCrossQuadratic`.

        Args:

            c_bar_1 (float): Critical concentration of species 1 at the onset of phase separation

            beta_tilde (float): Parameter associated with the quadratic term :math:`\\beta (c_1-1)^2` of species 1

            gamma_tilde (float): Parameter that describes the cross-interactions between the species
            :math:`\\tilde{\\gamma} \\tilde{c}_1 \\tilde{c}_2`

            lamda_tilde (float): Parameter that describes the self interaction of species 2 using
            :math:`\\tilde{\\lambda} \\tilde{c}^2_2`

            kappa_tilde (float): Parameter that describes the surface tension associated with species 1
            :math:`\\tilde{\\kappa}/2 |\\tilde{\\nabla} \\tilde{c}_1|^2`

            well_center (numpy.ndarray): Coordinates of the center of a Gaussian attractive well. 2d or 3D array

            well_depth (float): Depth of the Gaussian well

            sigma (float): Width of the Gaussian well
        """

        self._free_energy_type = 2

        # Ensure that the parameter lambda is always positive
        # Otherwise, we will get nonsense results in the simulations
        assert lamda_tilde > 0, "The parameter lambda is negative. Please supply a positive value"

        # Assign all free energy parameters to private variables
        self._beta_tilde = beta_tilde
        self._gamma_tilde = gamma_tilde
        self._lambda_tilde = lamda_tilde
        self._kappa_tilde = kappa_tilde
        self._well_center = well_center
        self._well_depth = well_depth
        self._sigma = sigma
        self._c_bar_1 = c_bar_1

    @property
    def kappa(self):
        """Getter for the private variable self._kappa_tilde.
        This is used to set up the surface tension term in the dynamical equations"""
        return self._kappa_tilde

    def get_gaussian_function(self, mesh):
        """Function that calculates :math:`e^{-|\\vec{r}-\\vec{r}_0|^2/2\\sigma^2}`

        Args:
            mesh (fipy or Gmsh mesh): A mesh generated by fipy in-built functions or Gmsh

        Returns:
            gaussian_function (fipy.cellVariable): A variable storing the Gaussian function evaluated at each mesh point
        """
        # Get mesh dimensions from the CellVariables in c_vector
        mesh_dimensions = np.shape(mesh.cellCenters.value)[0]
        # Calculate distance of each mesh point from the center of the Gaussian well
        distance_squared_from_well_center = np.sum([(mesh.cellCenters[i] - self._well_center[i]) ** 2
                                                    for i in range(mesh_dimensions)], 0)
        gaussian_function = fp.CellVariable(mesh=mesh,
                                            value=np.exp(-distance_squared_from_well_center / (2 * self._sigma ** 2)))
        gaussian_function = self._well_depth * gaussian_function
        return gaussian_function

    def calculate_fe(self, c_vector):
        """Calculate free energy according to the expression in class description.

        Args:
            c_vector (numpy.ndarray): A 2x1 vector of species concentrations that looks like :math:`[c_1, c_2]`.
            The concentration variables :math:`c_1` and :math:`c_2` must be instances of the class
            :class:`fipy.CellVariable` or equivalent. These instances should have an attribute called :attr:`.grad.mag`
            that returns the magnitude of gradient of the concentration field for every position in the mesh to compute
            the surface tension contribution of the free energy

        Returns:
            free_energy (fipy.cellVariable): Free energy value
        """

        # Check that c_vector satisfies the necessary conditions
        assert len(c_vector) == 2, \
            "The shape of c_vector passed to TwoCompDoubleWellFHCrossQuadratic.calculate_fe() is not 2x1"
        assert hasattr(c_vector[0], "grad"), \
            "The instance c_vector[0] has no attribute grad associated with it"
        assert hasattr(c_vector[1], "grad"), \
            "The instance c_vector[1] has no function grad associated with it"
        assert hasattr(c_vector[0].grad, 'mag'), \
            "The instance c_vector[0].grad has no attribute mag associated with it"
        assert hasattr(c_vector[1].grad, 'mag'), \
            "The instance c_vector[1].grad has no attribute mag associated with it"

        # Calculate the free energy
        fe = (0.25 * (c_vector[0] - self._c_bar_1) ** 4
              + 0.5 * self._beta_tilde * (c_vector[0] - self._c_bar_1) ** 2
              - self.get_gaussian_function(c_vector[0].mesh) * c_vector[0]
              + self._gamma_tilde * c_vector[0] * c_vector[1]
              + 0.5 * self._lambda_tilde * c_vector[1] ** 2
              + 0.5 * self._kappa_tilde * c_vector[0].grad.mag ** 2)

        return fe

    def calculate_mu(self, c_vector):
        """Calculate chemical potential of the species.

        Chemical potential of species 1:

        .. math::

            \\tilde{\\mu}_1[\\tilde{c}_1, \\tilde{c}_2] = \\delta \\tilde{f} / \\delta \\tilde{c}_1 =
            (\\tilde{c}_1-1)^3 + \\tilde{\\beta} (\\tilde{c}_1-1) + \\tilde{\\gamma} \\tilde{c}_2
            - \\tilde{\\kappa} \\tilde{\\nabla}^2 \\tilde{c}_1 - \\tilde{c} \\exp^{-|\\vec{r}-\\vec{r}|^2/2\\sigma^2}

        Chemical potential of species 2:

        .. math::

            \\tilde{\\mu}_2[\\tilde{c}_1, \\tilde{c}_2] = \\delta \\tilde{f} / \\delta \\tilde{c}_2
            = \\tilde{\\gamma} \\tilde{c}_1 + \\tilde{\\lambda} \\tilde{c}_2


        Args:
            c_vector (numpy.ndarray): A 2x1 vector of species concentrations that looks like :math:`[c_1, c_2]`. The
            concentration variables :math:`c_1` and :math:`c_2` must be instances of the class
            :class:`fipy.CellVariable` or equivalent. These instances should have an attribute called
            :attr:`.faceGrad.divergence` that returns the Laplacian of the concentration field for every position in the
            mesh to compute the surface tension contribution to the chemical potential of species 1

        Returns:
            mu (list): A 2x1 vector of chemical potentials that looks like :math:`[\\mu_1, \\mu_2]`
        """

        # Check that c_vector satisfies the necessary conditions
        assert len(c_vector) == 2, \
            "The shape of c_vector passed to TwoCompDoubleWellFHCrossQuadraticDimensionless.calculate_mu() is not 2x1"
        assert hasattr(c_vector[0], "faceGrad"), \
            "The instance c_vector[0] has no attribute faceGrad associated with it"
        assert hasattr(c_vector[1], "faceGrad"), \
            "The instance c_vector[1] has no attribute faceGrad associated with it"
        assert hasattr(c_vector[0].faceGrad, "divergence"), \
            "The instance c_vector[0].faceGrad has no attribute divergence associated with it"
        assert hasattr(c_vector[1].faceGrad, "divergence"), \
            "The instance c_vector[1].faceGrad has no attribute divergence associated with it"

        # Calculate the chemical potentials
        mu_1 = ((c_vector[0] - self._c_bar_1) ** 3
                + self._beta_tilde * (c_vector[0] - self._c_bar_1)
                - self.get_gaussian_function(c_vector[0].mesh)
                + self._gamma_tilde * c_vector[1]
                - self._kappa_tilde * c_vector[0].faceGrad.divergence)
        mu_2 = self._gamma_tilde * c_vector[0] + self._lambda_tilde * c_vector[1]
        mu = [mu_1, mu_2]

        return mu

    def calculate_mu_1_bulk(self, c_vector):
        """Calculate chemical potential associated with bulk free energy of species 1 with the double well potential

        Bulk chemical potential of species 1:

        .. math::

            \\tilde{\\mu}_1[\\tilde{c}_1, \\tilde{c}_2] = \\delta \\tilde{f} / \\delta \\tilde{c}_1 =
            (\\tilde{c}_1-1)^3 + \\tilde{\\beta} (\\tilde{c}_1-1) + \\tilde{\\gamma} \\tilde{c}_2
            - \\tilde{c} \\exp^{-|\\vec{r}-\\vec{r}|^2/2\\sigma^2}


        Args:
            c_vector (numpy.ndarray): A 2x1 vector of species concentrations that looks like :math:`[c_1, c_2]`. The
            concentration variables :math:`c_1` and :math:`c_2` must be instances of the class
            :class:`fipy.CellVariable` or equivalent. These instances should have an attribute called
            :attr:`.faceGrad.divergence` that returns the Laplacian of the concentration field for every position in the
            mesh to compute the surface tension contribution to the chemical potential of species 1

        Returns:
            mu_1 (fipy.CellVariable): The chemical potential :math:`\\mu_1[\\tilde{c}_1, \\tilde{c}_2]`
        """

        # Check that c_vector satisfies the necessary conditions
        assert len(c_vector) == 2, \
            "The shape of c_vector passed to TwoCompDoubleWellFHCrossQuadraticDimensionless.calculate_mu() is not 2x1"

        # Calculate the chemical potentials
        mu_1 = ((c_vector[0] - self._c_bar_1) ** 3
                + self._beta_tilde * (c_vector[0] - self._c_bar_1)
                - self.get_gaussian_function(c_vector[0].mesh)
                + self._gamma_tilde * c_vector[1])

        return mu_1

    def calculate_jacobian(self, c_vector):
        """Calculate the Jacobian matrix of coefficients to feed to the transport equations.

        In calculating the Jacobian, we ignore the surface tension and any spatially dependent terms and only take the
        bulk part of the free energy that depends on the concentration fields:

        .. math::
            J_{11} = \\delta^2 \\tilde{f}_{bulk} / \\delta \\tilde{c}^2_1 = 3 (\\tilde{c}_1 - 1)^2 + \\tilde{\\beta}

        .. math::
            J_{12} = \\delta^2 \\tilde{f}_{bulk} / \\delta \\tilde{c}_1 \\delta \\tilde{c}_2 = \\tilde{\\gamma}

        .. math::
            J_{21} = \\delta^2 \\tilde{f}_{bulk} / \\delta \\tilde{c}_1 \\delta \\tilde{c}_2 = \\tilde{\\gamma}

        .. math::
            J_{22} = \\delta^2 \\tilde{f}_{bulk} / \\delta \\tilde{c}^2_2 = \\tilde{\\lambda}

        Args:
            c_vector (numpy.ndarray): A 2x1 vector of species concentrations that looks like :math:`[c_1, c_2]`.The
            concentration variables :math:`c_1` and :math:`c_2` must be instances of the class
            :class:`fipy.CellVariable` or equivalent
        Returns:
            jacobian (numpy.ndarray): A 2x2 Jacobian matrix, with each entry itself being a vector of the same size as
            c_vector[0]
        """

        # Check that c_vector satisfies the necessary conditions
        assert len(c_vector) == 2, \
            "The shape of c_vector passed to TwoCompDoubleWellFHCrossQuadraticDimensionless.calculate_jacobian() \
            is not 2x1"

        # Calculate the Jacobian matrix
        jacobian = [[3 * (c_vector[0] - self._c_bar_1) ** 2 + self._beta_tilde, self._gamma_tilde],
                             [self._gamma_tilde/self._lambda_tilde, 1.0]]
        return jacobian

class TwoCompDoubleWellFHCrossQuadraticDimensionlessCoupled(object):

    def __init__(self, c_bar_1, beta_tilde, gamma_tilde, lamda_tilde, chiPR_tilde, kappa_tilde, well_center, well_depth, sigma, k_tilde, r_p, rest_length):
        """Initialize an object of :class:`TwoCompDoubleWellFHCrossQuadratic`.

        Args:

            c_bar_1 (float): Critical concentration of species 1 at the onset of phase separation

            beta_tilde (float): Parameter associated with the quadratic term :math:`\\beta (c_1-1)^2` of species 1

            gamma_tilde (float): Parameter that describes the cross-interactions between the species
            :math:`\\tilde{\\gamma} \\tilde{c}_1 \\tilde{c}_2`

            lamda_tilde (float): Parameter that describes the self interaction of species 2 using
            :math:`\\tilde{\\lambda} \\tilde{c}^2_2`

            kappa_tilde (float): Parameter that describes the surface tension associated with species 1
            :math:`\\tilde{\\kappa}/2 |\\tilde{\\nabla} \\tilde{c}_1|^2`

            well_center (numpy.ndarray): Coordinates of the center of a Gaussian attractive well. 2d or 3D array

            well_depth (float): Depth of the Gaussian well

            sigma (float): Width of the Gaussian well
        """

        self._free_energy_type = 3

        # Ensure that the parameter lambda is always positive
        # Otherwise, we will get nonsense results in the simulations
        assert lamda_tilde > 0, "The parameter lambda is negative. Please supply a positive value"

        # Assign all free energy parameters to private variables
        self._beta_tilde = beta_tilde
        self._gamma_tilde = gamma_tilde
        self._lambda_tilde = lamda_tilde
        self._kappa_tilde = kappa_tilde
        self._chiPR_tilde = chiPR_tilde
        self._well_center = well_center
        self._well_depth = well_depth
        self._sigma = sigma
        self._c_bar_1 = c_bar_1
        self._k_tilde = k_tilde
        self._r_p = r_p
        self._rest_length = rest_length

    @property
    def kappa(self):
        """Getter for the private variable self._kappa_tilde.
        This is used to set up the surface tension term in the dynamical equations"""
        return self._kappa_tilde

    def get_gaussian_function(self, mesh, well_center):
        """Function that calculates :math:`e^{-|\\vec{r}-\\vec{r}_0|^2/2\\sigma^2}`

        Args:
            mesh (fipy or Gmsh mesh): A mesh generated by fipy in-built functions or Gmsh

        Returns:
            gaussian_function (fipy.cellVariable): A variable storing the Gaussian function evaluated at each mesh point
        """
        # Get mesh dimensions from the CellVariables in c_vector
        mesh_dimensions = np.shape(mesh.cellCenters.value)[0]
        # Calculate distance of each mesh point from the center of the Gaussian well
        distance_squared_from_well_center = np.sum([(mesh.cellCenters[i] - well_center[i]) ** 2
                                                    for i in range(mesh_dimensions)], 0)
        gaussian_function = fp.CellVariable(mesh=mesh,
                                            value=np.exp(-distance_squared_from_well_center / (2 * self._sigma ** 2)))
        gaussian_function = self._well_depth * gaussian_function
        return gaussian_function

    def calculate_fe(self, c_vector, well_center):
        """Calculate free energy according to the expression in class description.

        Args:
            c_vector (numpy.ndarray): A 2x1 vector of species concentrations that looks like :math:`[c_1, c_2]`.
            The concentration variables :math:`c_1` and :math:`c_2` must be instances of the class
            :class:`fipy.CellVariable` or equivalent. These instances should have an attribute called :attr:`.grad.mag`
            that returns the magnitude of gradient of the concentration field for every position in the mesh to compute
            the surface tension contribution of the free energy

        Returns:
            free_energy (fipy.cellVariable): Free energy value
        """

        # Check that c_vector satisfies the necessary conditions
        # assert len(c_vector) == 2, \ 
            # "The shape of c_vector passed to TwoCompDoubleWellFHCrossQuadratic.calculate_fe() is not 2x1"
        assert hasattr(c_vector[0], "grad"), \
            "The instance c_vector[0] has no attribute grad associated with it"
        assert hasattr(c_vector[1], "grad"), \
            "The instance c_vector[1] has no function grad associated with it"
        assert hasattr(c_vector[0].grad, 'mag'), \
            "The instance c_vector[0].grad has no attribute mag associated with it"
        assert hasattr(c_vector[1].grad, 'mag'), \
            "The instance c_vector[1].grad has no attribute mag associated with it"

        # Calculate the free energy
        fe = (0.25 * (c_vector[0] - self._c_bar_1) ** 4
              + 0.5 * self._beta_tilde * (c_vector[0] - self._c_bar_1) ** 2
              - self.get_gaussian_function(c_vector[0].mesh, well_center) * c_vector[0]
              + self._gamma_tilde * c_vector[0] * c_vector[1]
              + 0.5 * self._lambda_tilde * c_vector[1] ** 2
              + 0.5 * self._chiPR_tilde * c_vector[0] ** 2 * c_vector[1] ** 2
              + 0.5 * self._kappa_tilde * c_vector[0].grad.mag ** 2)

        return fe

    def calculate_mu(self, c_vector, well_center):
        """Calculate chemical potential of the species.

        Chemical potential of species 1:

        .. math::

            \\tilde{\\mu}_1[\\tilde{c}_1, \\tilde{c}_2] = \\delta \\tilde{f} / \\delta \\tilde{c}_1 =
            (\\tilde{c}_1-1)^3 + \\tilde{\\beta} (\\tilde{c}_1-1) + \\tilde{\\gamma} \\tilde{c}_2
            - \\tilde{\\kappa} \\tilde{\\nabla}^2 \\tilde{c}_1 - \\tilde{c} \\exp^{-|\\vec{r}-\\vec{r}|^2/2\\sigma^2}

        Chemical potential of species 2:

        .. math::

            \\tilde{\\mu}_2[\\tilde{c}_1, \\tilde{c}_2] = \\delta \\tilde{f} / \\delta \\tilde{c}_2
            = \\tilde{\\gamma} \\tilde{c}_1 + \\tilde{\\lambda} \\tilde{c}_2


        Args:
            c_vector (numpy.ndarray): A 2x1 vector of species concentrations that looks like :math:`[c_1, c_2]`. The
            concentration variables :math:`c_1` and :math:`c_2` must be instances of the class
            :class:`fipy.CellVariable` or equivalent. These instances should have an attribute called
            :attr:`.faceGrad.divergence` that returns the Laplacian of the concentration field for every position in the
            mesh to compute the surface tension contribution to the chemical potential of species 1

        Returns:
            mu (list): A 2x1 vector of chemical potentials that looks like :math:`[\\mu_1, \\mu_2]`
        """

        # Check that c_vector satisfies the necessary conditions
        # assert len(c_vector) == 2, \
            # "The shape of c_vector passed to TwoCompDoubleWellFHCrossQuadraticDimensionless.calculate_mu() is not 2x1"
        assert hasattr(c_vector[0], "faceGrad"), \
            "The instance c_vector[0] has no attribute faceGrad associated with it"
        assert hasattr(c_vector[1], "faceGrad"), \
            "The instance c_vector[1] has no attribute faceGrad associated with it"
        assert hasattr(c_vector[0].faceGrad, "divergence"), \
            "The instance c_vector[0].faceGrad has no attribute divergence associated with it"
        assert hasattr(c_vector[1].faceGrad, "divergence"), \
            "The instance c_vector[1].faceGrad has no attribute divergence associated with it"

        # Calculate the chemical potentials
        mu_1 = ((c_vector[0] - self._c_bar_1) ** 3
                + self._beta_tilde * (c_vector[0] - self._c_bar_1)
                - self.get_gaussian_function(c_vector[0].mesh, well_center)
                + self._gamma_tilde * c_vector[1]
                + self._chiPR_tilde * c_vector[0] * c_vector[1] ** 2
                - self._kappa_tilde * c_vector[0].faceGrad.divergence)
        mu_2 = self._gamma_tilde * c_vector[0] + self._lambda_tilde * c_vector[1] + self._chiPR_tilde * c_vector[0] ** 2 * c_vector[1]
        mu = [mu_1, mu_2]

        return mu

    def calculate_jacobian(self, c_vector):
        """Calculate the Jacobian matrix of coefficients to feed to the transport equations.

        In calculating the Jacobian, we ignore the surface tension and any spatially dependent terms and only take the
        bulk part of the free energy that depends on the concentration fields:

        .. math::
            J_{11} = \\delta^2 \\tilde{f}_{bulk} / \\delta \\tilde{c}^2_1 = 3 (\\tilde{c}_1 - 1)^2 + \\tilde{\\beta}

        .. math::
            J_{12} = \\delta^2 \\tilde{f}_{bulk} / \\delta \\tilde{c}_1 \\delta \\tilde{c}_2 = \\tilde{\\gamma}

        .. math::
            J_{21} = \\delta^2 \\tilde{f}_{bulk} / \\delta \\tilde{c}_1 \\delta \\tilde{c}_2 = \\tilde{\\gamma}

        .. math::
            J_{22} = \\delta^2 \\tilde{f}_{bulk} / \\delta \\tilde{c}^2_2 = \\tilde{\\lambda}

        Args:
            c_vector (numpy.ndarray): A 2x1 vector of species concentrations that looks like :math:`[c_1, c_2]`.The
            concentration variables :math:`c_1` and :math:`c_2` must be instances of the class
            :class:`fipy.CellVariable` or equivalent
        Returns:
            jacobian (numpy.ndarray): A 2x2 Jacobian matrix, with each entry itself being a vector of the same size as
            c_vector[0]
        """

        # Check that c_vector satisfies the necessary conditions
        # assert len(c_vector) == 2, \
            # "The shape of c_vector passed to TwoCompDoubleWellFHCrossQuadraticDimensionless.calculate_jacobian() \
            # is not 2x1"

        # Calculate the Jacobian matrix
        jacobian = [[3 * (c_vector[0] - self._c_bar_1) ** 2 + self._beta_tilde + self._chiPR_tilde * c_vector[1] ** 2, self._gamma_tilde + 2 * self._chiPR_tilde * c_vector[0] * c_vector[1]],
                             [self._gamma_tilde + 2 * self._chiPR_tilde * c_vector[0] * c_vector[1], self._lambda_tilde + self._chiPR_tilde * c_vector[0] ** 2]]
        return jacobian