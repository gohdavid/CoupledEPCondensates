"""Module that assembles the model equations for spatiotemporal dynamics of concentration fields.
"""

import fipy as fp
import numpy as np
from . import reaction_rates as rates

class DelayTracker:
    def __init__(self, steps, tau):
        self.head = 0
        self.tau = tau
        self.concentrations = [None]*steps
        self.times = np.ones(steps)*np.inf
    def record(self, time, concentration, step):
        self.concentrations[step] = concentration
        self.times[step] = time
    def find_closest(self,time):
        return np.argmin((self.times-time)**2)
    def get_delay(self, time):
        index = self.find_closest(time-self.tau)
        self.delayed_concentration = self.concentrations[index]
        self.concentrations[self.head:index] = [None]*(index-self.head)
        self.head = index
        return index

class TwoComponentModel(object):
    """Two component system, with Model B for species 1 and Model AB or reaction-diffusion with reactions for species 2

    This class describes the spatiotemporal dynamics of concentration fields two component system given by the below
    expression:

    .. math::

        \\partial c_1 / \\partial t = \\nabla (M_1 \\nabla \\mu_1 (c_1, c_2))

        \\partial c_2 / \\partial t = \\nabla (M_2 \\nabla \\mu_2 (c_1, c_2)) + k_1 c_1 - k_2 c_2

        (or)

        \\partial c_2 / \\partial t = \\nabla (M_2 \\nabla c_2) + k_1 c_1 - k_2 c_2

    Species 1 relaxes via Model B dynamics, with a mobility coefficient :math:`M_1`. It's total amount in the domain is
    conserved.

    Species 2 undergoes a Model AB or reaction-diffusion dynamics. Detailed balance is broken in this equation.
    It's mobility coefficient is :math:`M_2` and is produced by species 1 with a rate constant :math:`k_1` and degrades
    with a rate constant :math:`k_2`
    """

    def __init__(self, mobility_1, mobility_2, mobility_3, modelAB_dynamics_type, degradation_constant, free_energy):
        """Initialize an object of :class:`TwoComponentModelBModelAB`.

        Args:
            mobility_1 (float): Mobility of species 1

            mobility_2 (float): Mobility of species 2

            modelAB_dynamics_type (integer): If = 1, Model AB dynamics. If = 2, reaction-diffusion for species 2.

            degradation_constant (float): Rate constant for first-order degradation of species 2

            free_energy: An instance of one of the free energy classes present in :mod:`utils.free_energy`

            c_vector (numpy.ndarray): A 2x1 vector of species concentrations that looks like :math:`[c_1, c_2]`.

            The concentration variables :math:`c_1` and :math:`c_2` must be instances of the class
            :class:`fipy.CellVariable`
        """

        # Parameters of the dynamical equations
        self._M1 = mobility_1
        self._M2 = mobility_2
        # Localization locus dynamics
        self._M3 = mobility_3
        self._modelAB_dynamics_type = modelAB_dynamics_type
        self._free_energy = free_energy
        # Define the reaction terms in the model equations
        self._production_term = None
        self._degradation_term = rates.FirstOrderReaction(k=degradation_constant)
        # Define model equations
        self._equations = None
        # The fipy solver used to solve the model equations
        self._solver = None

    def set_production_term(self, reaction_type, **kwargs):
        """ Sets the nature of the production term of species :math:`c_2` from :math:`c_1`

        If reaction_type == 1: First order reaction with rate constant uniform in space.

        If reaction_type == 2: First order reaction with rate constant Gaussian in space. This requires the parameter
        sigma (width of Gaussian), coordinates of the center point of Gaussian, and the mesh geometry as optional input
        arguments to compute rate constant at every position in space.

        Args:
            reaction_type (integer): An integer value describing what reaction type to consider.
        """
        if reaction_type == 1:
            # Reaction rate constant is uniform in space
            rate_constant = kwargs.get('rate_constant', None)
            self._production_term = rates.FirstOrderReaction(k=rate_constant)
        elif reaction_type == 2:
            # Reaction rate constant is Gaussian in space
            basal_rate_constant = kwargs.get('basal_rate_constant', None)
            rate_constant = kwargs.get('rate_constant', None)
            sigma = kwargs.get('sigma', None)
            center_point = kwargs.get('center_point', None)
            geometry = kwargs.get('geometry', None)
            self._production_term = rates.LocalizedFirstOrderReaction(k0=basal_rate_constant, k=rate_constant,
                                                                      sigma=sigma, x0=center_point,
                                                                      simulation_geometry=geometry)

    def set_model_equations(self, c_vector, well_center):
        """Assemble the model equations given a mesh and concentrations

        This functions assembles the model equations necessary

        Args:
            c_vector (numpy.ndarray): A 2x1 vector of species concentrations that looks like :math:`[c_1, c_2]`.
            The concentration variables :math:`c_1` and :math:`c_2` must be instances of the class
            :class:`fipy.CellVariable`

        Assigns:
            self._equations (list): List that would go to 0 if the concentrations in c_vector satisfy the model equation
        """

        # Get Jacobian matrix associated with the free energy. This gives us the coefficients that multiply the
        # gradients of the concentration fields in the Model B dynamics.
        assert hasattr(self._free_energy, 'calculate_jacobian'), \
            "self._free_energy instance does not have a function calculate_jacobian()"
        assert hasattr(self._free_energy, '_kappa') or hasattr(self._free_energy, '_kappa_tilde'), \
            "self._free_energy instance does not have an attribute kappa describing the surface energy"

        jacobian = self._free_energy.calculate_jacobian(c_vector)

        eqn_1 = (fp.TransientTerm(coeff=1.0, var=c_vector[0])
                 == fp.DiffusionTerm(coeff=self._M1 * jacobian[0][0], var=c_vector[0])
                 + fp.DiffusionTerm(coeff=self._M1 * jacobian[0][1], var=c_vector[1])
                 - fp.DiffusionTerm(coeff=(self._M1, self._free_energy.kappa), var=c_vector[0])
                 - self._M1 * (self._free_energy.get_gaussian_function(c_vector[0].mesh, well_center)).faceGrad.divergence
                 )

        # Model AB dynamics or reaction-diffusion dynamics for species 2 with production and degradation reactions
        if self._modelAB_dynamics_type == 1:
            # Model AB dynamics for species 2
            eqn_2 = (fp.TransientTerm(var=c_vector[1])
                     == fp.DiffusionTerm(coeff=self._M2 * jacobian[1][0], var=c_vector[0])
                     + fp.DiffusionTerm(coeff=self._M2 * jacobian[1][1], var=c_vector[1])
                     + self._production_term.rate(c_vector[0])
                     - self._degradation_term.rate(c_vector[1])
                     )
        elif self._modelAB_dynamics_type == 2:
            # Reaction-diffusion dynamics for species 2
            eqn_2 = (fp.TransientTerm(var=c_vector[1])
                     == fp.DiffusionTerm(coeff=self._M2 * jacobian[1][1], var=c_vector[1])
                     + self._production_term.rate(c_vector[0])
                     - self._degradation_term.rate(c_vector[1])
                     )

        # Localization locus dynamics
        self._eqn_locus_x = [self._M3*(self._free_energy._well_depth  * c_vector[0] * (c_vector[0].mesh.x-well_center[0]) / (self._free_energy._sigma**2) * np.exp(-((c_vector[0].mesh.x-well_center[0])**2 + (c_vector[0].mesh.y-well_center[1])**2) / (2*self._free_energy._sigma**2)) * c_vector[0].mesh.cellVolumes).sum(),
                           - self._M3 * self._free_energy._k_tilde *(well_center[0] - self._free_energy._r_p[0] - self._free_energy._rest_length[0])]
        self._eqn_locus_y = [self._M3*(self._free_energy._well_depth  * c_vector[0] * (c_vector[0].mesh.y-well_center[1]) / (self._free_energy._sigma**2) * np.exp(-((c_vector[0].mesh.x-well_center[0])**2 + (c_vector[0].mesh.y-well_center[1])**2) / (2*self._free_energy._sigma**2)) * c_vector[0].mesh.cellVolumes).sum(),
                           - self._M3 * self._free_energy._k_tilde *(well_center[1] - self._free_energy._r_p[1] - self._free_energy._rest_length[1])]
        self._equations = [eqn_1, eqn_2, self._eqn_locus_x[0]+self._eqn_locus_x[1], self._eqn_locus_y[0]+self._eqn_locus_y[1]]

        # Define the relative tolerance of the fipy solver
        self._solver = fp.DefaultSolver(tolerance=1e-10, iterations=2000)

    def step_once(self, c_vector, well_center, dt, max_residual, max_sweeps):
        """Function that solves the model equations over a time step of dt to get the concentration profiles.

        Args:
            c_vector (numpy.ndarray): A 2x1 vector of species concentrations that looks like :math:`[c_1, c_2]`.
            The concentration variables :math:`c_1` and :math:`c_2` must be instances of the class
            :class:`fipy.CellVariable`

            dt (float): Size of time step to solve the model equations over once

            max_residual (float): Maximum value of the residual acceptable when sweeping the equations

            max_sweeps (int): Maximum number of sweeps before stopping

        Returns:
            has_converged (bool): A true / false value answering if the sweeps have converged

            residuals (numpy.ndarray): A 2x1 numpy array containing residuals after solving the equations

            max_change (float): Maximum change in the concentration fields at any given position for the time interval
            dt

        """
        # Solve for the locus position with a time step of 0.1*dt using the Euler method
        for small_step in range(10):
            self.set_model_equations(c_vector, well_center)
            well_center[0].setValue(well_center[0]+self._equations[2]*dt/10)
            well_center[1].setValue(well_center[1]+self._equations[3]*dt/10)

        # Solve the model equations for a time step of dt by sweeping max_sweeps times
        residual_1 = 1e6
        residual_2 = 1e6
        residual_3 = 1e6
        has_converged = False

        # Strang Splitting
        for i in range(max_sweeps):
            residual_1 = self._equations[0].sweep(dt=0.5*dt, var=c_vector[0], solver=self._solver)
            if np.max(residual_1) < max_residual:
                break
        max_change_c_1 = np.max(np.abs((c_vector[0] - c_vector[0].old).value))
        c_vector[0].updateOld()

        for i in range(max_sweeps):
            residual_2 = self._equations[1].sweep(dt=dt, var=c_vector[1], solver=self._solver)
            if np.max(residual_2) < max_residual:
                break
        max_change_c_2 = np.max(np.abs((c_vector[1] - c_vector[1].old).value))
        c_vector[1].updateOld()

        for i in range(max_sweeps):
            residual_3 = self._equations[0].sweep(dt=0.5*dt, var=c_vector[0], solver=self._solver)
            if np.max(residual_3) < max_residual:
                break
        max_change_c_1 = np.max([max_change_c_1, np.max(np.abs((c_vector[0] - c_vector[0].old).value))])
        c_vector[0].updateOld()

        residuals = np.array([residual_1, residual_2, residual_3])
        if np.max(residuals) < max_residual:
            has_converged = True
        max_change = np.max([max_change_c_1, max_change_c_2])

        return has_converged, residuals, max_change

    def step_once_old_2(self, c_vector, dt, max_sweeps):
        """Function that solves the model equations over a time step of dt to get the concentration profiles.

        Args:
            c_vector (numpy.ndarray): A 2x1 vector of species concentrations that looks like :math:`[c_1, c_2]`.
            The concentration variables :math:`c_1` and :math:`c_2` must be instances of the class
            :class:`fipy.CellVariable`

            dt (float): Size of time step to solve the model equations over once

            max_sweeps (int): Number of times to sweep using the function sweep() in the fipy package

        Returns:
            residuals (numpy.ndarray): A 2x1 numpy array containing residuals after solving the equations

            max_change (float): Maximum change in the concentration fields at any given position for the time interval
            dt

        """

        # Solve the model equations for a time step of dt by sweeping max_sweeps times
        residual_1 = 1e6
        residual_2 = 1e6
        residual_3 = 1e6

        # Split the non-linear operator separately from the linear operators and use Strang splitting to get second
        # order accuracy
        # eqn = (self._equations[0] & self._equations[1])

        for i in range(max_sweeps):
            residual_1 = self._equations[2].sweep(dt=0.5*dt, var=c_vector[0])
        c_vector[0].updateOld()
        for i in range(max_sweeps):
            residual_2 = self._equations[0].sweep(dt=dt)
        # residual_2 = eqn.solve(dt=dt)
            residual_3 = self._equations[1].sweep(dt=dt)
        self.update_old(c_vector=c_vector)
        for i in range(max_sweeps):
            residual_4 = self._equations[2].sweep(dt=0.5*dt, var=c_vector[0])

        residuals = np.array([residual_1, residual_2, residual_3, residual_4])

        max_change_c_1 = np.max(np.abs((c_vector[0] - c_vector[0].old).value))
        max_change_c_2 = np.max(np.abs((c_vector[1] - c_vector[1].old).value))
        max_change = np.max([max_change_c_1, max_change_c_2])

        return residuals, max_change

    def step_once_old(self, c_vector, dt, max_sweeps):
        """Function that solves the model equations over a time step of dt to get the concentration profiles.

        Args:
            c_vector (numpy.ndarray): A 2x1 vector of species concentrations that looks like :math:`[c_1, c_2]`.
            The concentration variables :math:`c_1` and :math:`c_2` must be instances of the class
            :class:`fipy.CellVariable`

            dt (float): Size of time step to solve the model equations over once

            max_sweeps (int): Number of times to sweep using the function sweep() in the fipy package

        Returns:
            residuals (numpy.ndarray): A 2x1 numpy array containing residuals after solving the equations

            max_change (float): Maximum change in the concentration fields at any given position for the time interval
            dt

        """

        # Solve the model equations for a time step of dt by sweeping max_sweeps times
        residual_1 = 1e6
        residual_2 = 1e6
        residual_3 = 1e6

        # Strang Splitting
        for i in range(max_sweeps):
            residual_1 = self._equations[1].sweep(dt=0.5*dt, var=c_vector[1], solver=self._solver)
        c_vector[1].updateOld()
        for i in range(max_sweeps):
            residual_2 = self._equations[0].sweep(dt=dt, var=c_vector[0], solver=self._solver)
        c_vector[0].updateOld()
        for i in range(max_sweeps):
            residual_3 = self._equations[1].sweep(dt=0.5*dt, var=c_vector[1], solver=self._solver)

        residuals = np.array([residual_1, residual_2, residual_3])

        max_change_c_1 = np.max(np.abs((c_vector[0] - c_vector[0].old).value))
        max_change_c_2 = np.max(np.abs((c_vector[1] - c_vector[1].old).value))
        max_change = np.max([max_change_c_1, max_change_c_2])

        return residuals, max_change

    def update_old(self, c_vector):
        for i in range(len(c_vector)):
            c_vector[i].updateOld()
        # self._psi.updateOld()

class ThreeComponentModel(object):
    """Two component system, with Model B for species 1 and Model AB or reaction-diffusion with reactions for species 2

    This class describes the spatiotemporal dynamics of concentration fields two component system given by the below
    expression:

    .. math::

        \\partial c_1 / \\partial t = \\nabla (M_1 \\nabla \\mu_1 (c_1, c_2))

        \\partial c_2 / \\partial t = \\nabla (M_2 \\nabla \\mu_2 (c_1, c_2)) + k_1 c_1 - k_2 c_2

        (or)

        \\partial c_2 / \\partial t = \\nabla (M_2 \\nabla c_2) + k_1 c_1 - k_2 c_2

    Species 1 relaxes via Model B dynamics, with a mobility coefficient :math:`M_1`. It's total amount in the domain is
    conserved.

    Species 2 undergoes a Model AB or reaction-diffusion dynamics. Detailed balance is broken in this equation.
    It's mobility coefficient is :math:`M_2` and is produced by species 1 with a rate constant :math:`k_1` and degrades
    with a rate constant :math:`k_2`
    """

    def __init__(self, mobility_1, mobility_2, mobility_3, modelAB_dynamics_type, degradation_constant, free_energy, tau, total_steps):
        """Initialize an object of :class:`TwoComponentModelBModelAB`.

        Args:
            mobility_1 (float): Mobility of species 1

            mobility_2 (float): Mobility of species 2

            modelAB_dynamics_type (integer): If = 1, Model AB dynamics. If = 2, reaction-diffusion for species 2.

            degradation_constant (float): Rate constant for first-order degradation of species 2

            free_energy: An instance of one of the free energy classes present in :mod:`utils.free_energy`

            c_vector (numpy.ndarray): A 2x1 vector of species concentrations that looks like :math:`[c_1, c_2]`.

            The concentration variables : math:`c_1` and :math:`c_2` must be instances of the class
            :class:`fipy.CellVariable`
        """

        # Parameters of the dynamical equations
        self._M1 = mobility_1
        self._M2 = mobility_2
        # Localization locus dynamics
        self._M3 = mobility_3
        self._modelAB_dynamics_type = modelAB_dynamics_type
        self._free_energy = free_energy
        # Define the reaction terms in the model equations
        self._production_term = None
        self._degradation_term = rates.FirstOrderReaction(k=degradation_constant)
        # Define model equations
        self._equations = None
        # The fipy solver used to solve the model equations
        self._solver = None
        self.delay_tracker = DelayTracker(total_steps,tau)

    def set_production_term(self, reaction_type, **kwargs):
        """ Sets the nature of the production term of species :math:`c_2` from :math:`c_1`

        If reaction_type == 1: First order reaction with rate constant uniform in space.

        If reaction_type == 2: First order reaction with rate constant Gaussian in space. This requires the parameter
        sigma (width of Gaussian), coordinates of the center point of Gaussian, and the mesh geometry as optional input
        arguments to compute rate constant at every position in space.

        Args:
            reaction_type (integer): An integer value describing what reaction type to consider.
        """
        if reaction_type == 1:
            # Reaction rate constant is uniform in space
            rate_constant = kwargs.get('rate_constant', None)
            self._production_term = rates.FirstOrderReaction(k=rate_constant)
        elif reaction_type == 2:
            # Reaction rate constant is Gaussian in space
            basal_rate_constant = kwargs.get('basal_rate_constant', None)
            rate_constant = kwargs.get('rate_constant', None)
            sigma = kwargs.get('sigma', None)
            center_point = kwargs.get('center_point', None)
            geometry = kwargs.get('geometry', None)
            self._production_term = rates.LocalizedFirstOrderReaction(k0=basal_rate_constant, k=rate_constant,
                                                                      sigma=sigma, x0=center_point,
                                                                      simulation_geometry=geometry)

    def set_model_equations(self, c_vector, well_center):
        """Assemble the model equations given a mesh and concentrations

        This functions assembles the model equations necessary

        Args:
            c_vector (numpy.ndarray): A 2x1 vector of species concentrations that looks like :math:`[c_1, c_2]`.
            The concentration variables :math:`c_1` and :math:`c_2` must be instances of the class
            :class:`fipy.CellVariable`

        Assigns:
            self._equations (list): List that would go to 0 if the concentrations in c_vector satisfy the model equation
        """

        # Get Jacobian matrix associated with the free energy. This gives us the coefficients that multiply the
        # gradients of the concentration fields in the Model B dynamics.
        assert hasattr(self._free_energy, 'calculate_jacobian'), \
            "self._free_energy instance does not have a function calculate_jacobian()"
        assert hasattr(self._free_energy, '_kappa') or hasattr(self._free_energy, '_kappa_tilde'), \
            "self._free_energy instance does not have an attribute kappa describing the surface energy"

        jacobian = self._free_energy.calculate_jacobian(c_vector)

        eqn_1 = (fp.TransientTerm(coeff=1.0, var=c_vector[0])
                 == fp.DiffusionTerm(coeff=self._M1 * jacobian[0][0], var=c_vector[0])
                 + fp.DiffusionTerm(coeff=self._M1 * jacobian[0][1], var=c_vector[1])
                 - fp.DiffusionTerm(coeff=(self._M1, self._free_energy.kappa), var=c_vector[0])
                 - self._M1 * (self._free_energy.get_gaussian_function(c_vector[0].mesh, well_center)).faceGrad.divergence
                 )

        # Model AB dynamics or reaction-diffusion dynamics for species 2 with production and degradation reactions
        if self._modelAB_dynamics_type == 1:
            # Model AB dynamics for species 2
            eqn_2 = (fp.TransientTerm(var=c_vector[1])
                     == fp.DiffusionTerm(coeff=self._M2 * jacobian[1][0], var=c_vector[0])
                     + fp.DiffusionTerm(coeff=self._M2 * jacobian[1][1], var=c_vector[1])
                     + self._production_term.rate(c_vector[0])
                     - self._degradation_term.rate(c_vector[1])
                     )
        elif self._modelAB_dynamics_type == 2:
            # Reaction-diffusion dynamics for species 2
            eqn_2 = (fp.TransientTerm(var=c_vector[1])
                     == fp.DiffusionTerm(coeff=self._M2 * jacobian[1][1], var=c_vector[1])
                     + self._production_term.rate(c_vector[0])
                     - self._degradation_term.rate(c_vector[1])
                     )
        
        # Memory kernel for active protein
        eqn_3 = (fp.TransientTerm(coeff=self._tau, var=c_vector[2])
                 == - c_vector[2] + c_vector[0]
                 )

        # Localization locus dynamics
        self._equations = [eqn_1, eqn_2, eqn_3]

        # Define the relative tolerance of the fipy solver
        self._solver = fp.DefaultSolver(tolerance=1e-10, iterations=2000)
    
    def set_locus_equations(self, c_vector, well_center):
        self._eqn_locus_x = [self._M3*(self._free_energy._well_depth  * c_vector[0] * (c_vector[0].mesh.x-well_center[0]) / (self._free_energy._sigma**2) * np.exp(-((c_vector[0].mesh.x-well_center[0])**2 + (c_vector[0].mesh.y-well_center[1])**2) / (2*self._free_energy._sigma**2)) * c_vector[0].mesh.cellVolumes).sum(),
                           - self._M3 * self._free_energy._k_tilde *(well_center[0] - self._free_energy._r_p[0] - self._free_energy._rest_length[0])]
        self._eqn_locus_y = [self._M3*(self._free_energy._well_depth  * c_vector[0] * (c_vector[0].mesh.y-well_center[1]) / (self._free_energy._sigma**2) * np.exp(-((c_vector[0].mesh.x-well_center[0])**2 + (c_vector[0].mesh.y-well_center[1])**2) / (2*self._free_energy._sigma**2)) * c_vector[0].mesh.cellVolumes).sum(),
                           - self._M3 * self._free_energy._k_tilde *(well_center[1] - self._free_energy._r_p[1] - self._free_energy._rest_length[1])]
        self._locus_equations = [self._eqn_locus_x[0]+self._eqn_locus_x[1], self._eqn_locus_y[0]+self._eqn_locus_y[1]]

    def step_once(self, c_vector, well_center, dt, max_residual, max_sweeps):
        """Function that solves the model equations over a time step of dt to get the concentration profiles.

        Args:
            c_vector (numpy.ndarray): A 2x1 vector of species concentrations that looks like :math:`[c_1, c_2]`.
            The concentration variables :math:`c_1` and :math:`c_2` must be instances of the class
            :class:`fipy.CellVariable`

            dt (float): Size of time step to solve the model equations over once

            max_residual (float): Maximum value of the residual acceptable when sweeping the equations

            max_sweeps (int): Maximum number of sweeps before stopping

        Returns:
            has_converged (bool): A true / false value answering if the sweeps have converged

            residuals (numpy.ndarray): A 2x1 numpy array containing residuals after solving the equations

            max_change (float): Maximum change in the concentration fields at any given position for the time interval
            dt

        """
        # Solve for the locus position with a time step of 1/ratio*dt using the Euler method
        ratio = 100
        for small_step in range(ratio):
            self.set_locus_equations(c_vector, well_center)
            well_center[0].setValue(well_center[0]+self._equations[0]*dt/ratio)
            well_center[1].setValue(well_center[1]+self._equations[1]*dt/ratio)

        # Solve the model equations for a time step of dt by sweeping max_sweeps times
        residual_1 = 1e6
        residual_2 = 1e6
        residual_3 = 1e6
        has_converged = False

        # Strang Splitting
        for i in range(max_sweeps):
            residual_1 = self._equations[0].sweep(dt=0.5*dt, var=c_vector[0], solver=self._solver)
            if np.max(residual_1) < max_residual:
                break
        max_change_c_1 = np.max(np.abs((c_vector[0] - c_vector[0].old).value))
        c_vector[0].updateOld()

        for i in range(max_sweeps):
            residual_2 = self._equations[1].sweep(dt=dt, var=c_vector[1], solver=self._solver)
            if np.max(residual_2) < max_residual:
                break
        max_change_c_2 = np.max(np.abs((c_vector[1] - c_vector[1].old).value))
        c_vector[1].updateOld()

        for i in range(max_sweeps):
            residual_3 = self._equations[0].sweep(dt=0.5*dt, var=c_vector[0], solver=self._solver)
            if np.max(residual_3) < max_residual:
                break
        max_change_c_1 = np.max([max_change_c_1, np.max(np.abs((c_vector[0] - c_vector[0].old).value))])
        c_vector[0].updateOld()
        
        for i in range(max_sweeps):
            residual_4 = self._equations[2].sweep(dt=dt, var=c_vector[2], solver=self._solver)
            if np.max(residual_4) < max_residual:
                break
        max_change_c_3 = np.max(np.abs((c_vector[2] - c_vector[2].old).value))
        c_vector[2].updateOld()

        residuals = np.array([residual_1, residual_2, residual_3, residual_4])
        if np.max(residuals) < max_residual:
            has_converged = True
        max_change = np.max([max_change_c_1, max_change_c_2, max_change_c_3])

        return has_converged, residuals, max_change
    def update_old(self, c_vector):
        for i in range(len(c_vector)):
            c_vector[i].updateOld()
        # self._psi.updateOld()

class OldThreeComponentModel(object):