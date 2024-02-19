"""Module that contains helper functions to run simulations that can be used by run_simulation.py
"""

from . import geometry
from . import initial_conditions
from . import free_energy
from . import dynamical_equations
import fipy as fp


def set_mesh_geometry(input_params):
    """Set the mesh geometry depending on the options in input_parameters

    Mesh geometry types currently supported include:
    Type 1: 2D circular mesh
    Type 2:

    Args:
        input_params (dict): Dictionary that contains input parameters. We are only interested in the key,value pairs
        that describe the mesh geometry

    Returns:
         simulation_geometry (Geometry): A class object from :module:`utils.geometry`
    """
    simulation_geometry = None

    # Geometry in 2 dimensions
    if input_params['dimension'] == 2:
        # 2D Circular geometry
        if input_params['circ_flag'] == 1:
            assert 'radius' in input_params.keys() and 'dx' in input_params.keys(), \
                "input_params dictionary doesn't have values corresponding to the domain radius and mesh size"
            simulation_geometry = geometry.CircularMesh2d(radius=input_params['radius'], cell_size=input_params['dx'])
        # 2D Square geometry
        else:
            assert 'length' in input_params.keys() and 'dx' in input_params.keys(), \
                "input_params dictionary doesn't have values corresponding to the domain length and mesh size"
            simulation_geometry = geometry.SquareMesh2d(length=input_params['length'], dx=input_params['dx'])
    # 3D rectangular geometry
    elif input_params['dimension'] == 3:
        assert 'length' in input_params.keys() and 'dx' in input_params.keys(), \
            "input_params dictionary doesn't have values corresponding to the domain length and mesh size"
        simulation_geometry = geometry.CubeMesh3d(length=input_params['length'], dx=input_params['dx'])

    return simulation_geometry

def initialize_concentrations(input_params, simulation_geometry):
    """Set initial conditions for the concentration profiles

    Args:
        input_params (dict): Dictionary that contains input parameters. We are only interested in the key,value pairs
        that describe the initial conditions

        simulation_geometry (Geometry): Instance of class from :module:`utils.geometry` that describes the mesh
        geometry.

    Returns:
        concentration_vector (numpy.ndarray): An nx1 vector of species concentrations that looks like
        :math:`[c_1, c_2, ... c_n]`. The concentration variables :math:`c_i` must be instances of the class
        :class:`fipy.CellVariable` or equivalent.
    """

    # Initialize concentration_vector
    concentration_vector = []

    for i in range(int(input_params['n_concentrations'])):
        # Initialize fipy.CellVariable
        concentration_variable = fp.CellVariable(mesh=simulation_geometry.mesh, name='c_{index}'.format(index=i),
                                                 hasOld=True, value=input_params['initial_values'][i])
        # Nucleate a seed of dense concentrations if necessary
        if input_params['nucleate_seed'][i] == 1:
            initial_conditions.nucleate_spherical_seed(concentration=concentration_variable,
                                                       value=input_params['seed_value'][i],
                                                       dimension=input_params['dimension'],
                                                       geometry=simulation_geometry,
                                                       nucleus_size=input_params['nucleus_size'][i],
                                                       location=input_params['location'][i])
        # Append the concentration variable to the
        concentration_vector.append(concentration_variable)
    # Add noise to the initial conditions. If input_params['initial_condition_noise_variance'] is 0, then no noise
    # is added.
    initial_conditions.add_noise_to_initial_conditions(c_vector=concentration_vector,
                                                       sigmas=input_params['initial_condition_noise_variance'],
                                                       random_seed=int(input_params['random_seed']))
    return concentration_vector

def initialize_well_center(input_params):
    well_center = input_params["well_center"]
    well_center_x = fp.Variable(name='well_center_x', value=well_center[0])
    well_center_y = fp.Variable(name='well_center_y', value=well_center[1])
    return [well_center_x, well_center_y]

def set_free_energy(input_params):
    """Set free energy of interactions

    Args:
        input_params (dict): Dictionary that contains input parameters. We are only interested in the key,value pairs
        that describe the free energy

    Returns:
        free_en (utils.free_energy): An instance of one of the classes in mod:`utils.free_energy`
    """

    free_en = None

    if input_params['free_energy_type'] == 1:
        free_en = free_energy.TwoCompDoubleWellFHCrossQuadratic(alpha=input_params['alpha'],
                                                                beta=input_params['beta'],
                                                                gamma=input_params['gamma'],
                                                                lamda=input_params['lamda'],
                                                                kappa=input_params['kappa'],
                                                                c_bar_1=input_params['c_bar'],
                                                                well_depth=input_params['well_depth'],
                                                                well_center=input_params['well_center'],
                                                                sigma=input_params['sigma'])
    elif input_params['free_energy_type'] == 2:
        free_en = free_energy.TwoCompDoubleWellFHCrossQuadraticDimensionless(c_bar_1=input_params['c_bar_1'],
                                                                             beta_tilde=input_params['beta_tilde'],
                                                                             gamma_tilde=input_params['gamma_tilde'],
                                                                             lamda_tilde=input_params['lamda_tilde'],
                                                                             kappa_tilde=input_params['kappa_tilde'],
                                                                             well_depth=input_params['well_depth'],
                                                                             well_center=input_params['well_center'],
                                                                             sigma=input_params['sigma'])
    elif input_params['free_energy_type'] == 3:
        free_en = free_energy.TwoCompDoubleWellFHCrossQuadraticDimensionlessCoupled(c_bar_1=input_params['c_bar_1'],
                                                                                    beta_tilde=input_params['beta_tilde'],
                                                                                    gamma_tilde=input_params['gamma_tilde'],
                                                                                    lamda_tilde=input_params['lamda_tilde'],
                                                                                    kappa_tilde=input_params['kappa_tilde'],
                                                                                    chiPR_tilde=input_params['chiPR_tilde'],
                                                                                    well_depth=input_params['well_depth'],
                                                                                    well_center=input_params['well_center'],
                                                                                    sigma=input_params['sigma'],
                                                                                    k_tilde=input_params['k_tilde'],
                                                                                    r_p=input_params['r_p'],
                                                                                    rest_length=input_params['rest_length'])
    return free_en

def set_model_equations(input_params, concentration_vector, well_center, free_en, simulation_geometry,target_file):
    """Set dynamical equations for the model

    Args:
        input_params (dict): Dictionary that contains input parameters. We are only interested in the key,value pairs
        that describe the parameters associated with the dynamical model

        concentration_vector (numpy.ndarray): An nx1 vector of species concentrations that looks like
        :math:`[c_1, c_2, ... c_n]`. The concentration variables :math:`c_i` must be instances of the class
        :class:`fipy.CellVariable` or equivalent.

        free_en (utils.free_energy): An instance of one of the classes in mod:`utils.free_energy`
        simulation_geometry (Geometry): Instance of class from :module:`utils.geometry` that describes the mesh
        geometry.

        simulation_geometry (Geometry): Instance of class from :module:`utils.geometry` that describes the mesh
        geometry.

    Returns:
        equations (utils.dynamical_equations): An instance of one of the classes in mod:`utils.dynamical_equations`
    """
    if input_params["model_type"] == 1:
        assert input_params["n_concentrations"] == 2, "TwoComponentModel only supports 2 concentrations"
        equations = dynamical_equations.TwoComponentModel(mobility_1=input_params['M1'],
                                                        mobility_2=input_params['M2'],
                                                        mobility_3=input_params['M3'],
                                                        modelAB_dynamics_type=input_params['modelAB_dynamics_type'],
                                                        degradation_constant=input_params['k_degradation'],
                                                        free_energy=free_en)

        if input_params['reaction_type'] == 1:
            equations.set_production_term(reaction_type=input_params['reaction_type'],
                                        rate_constant=input_params['basal_k_production'])

        elif input_params['reaction_type'] == 2:
            equations.set_production_term(reaction_type=input_params['reaction_type'],
                                        basal_rate_constant=input_params['basal_k_production'],
                                        rate_constant=input_params['k_production'],
                                        sigma=input_params['reaction_sigma'],
                                        center_point=input_params['reaction_center'],
                                        geometry=simulation_geometry)


        equations.set_model_equations(c_vector=concentration_vector,well_center=well_center)
    elif input_params["model_type"] == 2:
        assert input_params["n_concentrations"] == 3, "ThreeComponentModel only supports 3 concentrations"
        equations = dynamical_equations.ThreeComponentModel(mobility_1=input_params['M1'],
                                                        mobility_2=input_params['M2'],
                                                        mobility_3=input_params['M3'],
                                                        modelAB_dynamics_type=input_params['modelAB_dynamics_type'],
                                                        degradation_constant=input_params['k_degradation'],
                                                        free_energy=free_en,
                                                        tau=input_params['tau'],
                                                        target_file=target_file)

        if input_params['reaction_type'] == 1:
            equations.set_production_term(reaction_type=input_params['reaction_type'],
                                        rate_constant=input_params['basal_k_production'])

        elif input_params['reaction_type'] == 2:
            equations.set_production_term(reaction_type=input_params['reaction_type'],
                                        basal_rate_constant=input_params['basal_k_production'],
                                        rate_constant=input_params['k_production'],
                                        sigma=input_params['reaction_sigma'],
                                        center_point=input_params['reaction_center'],
                                        geometry=simulation_geometry)

        elif input_params['reaction_type'] == 3:
                    equations.set_production_term(reaction_type=input_params['reaction_type'],
                                                basal_rate_constant=input_params['basal_k_production'],
                                                rate_constant=input_params['k_production'],
                                                sigma=input_params['reaction_sigma'],
                                                center_point=input_params['reaction_center'],
                                                geometry=simulation_geometry,
                                                hill_c0=input_params['hill_c0'],
                                                hill_kd=input_params['hill_kd'],
                                                hill_vmax=input_params['hill_vmax'],
                                                hill_n=input_params['hill_n'],
                                                hill_v0=input_params['hill_v0'])

        equations.set_model_equations(c_vector=concentration_vector,well_center=well_center,total_steps=input_params['total_steps'])

    return equations

def get_output_dir_name(input_params):
    """Set output directory name for the given input parameters.

    Args:
        input_params (dict): Dictionary that contains input parameters

    Returns:
        output_dir (string): Name of the output directory including the important parameter names
    """
    output_dir = (f"M1_{str(input_params['M1'])}"
                  f"_b_{str(input_params['beta_tilde'])}"
                  f"_g_{str(input_params['gamma_tilde'])}"
                  f"_c_{str(input_params['chiPR_tilde'])}"
                  f"_k_{str(input_params['kappa_tilde'])}"
                  f"_kp_{str(input_params['k_production'])}"
                  f"_c1_{str(input_params['initial_values'][0])}"
                #   f"_noiseVar_{str(input_params['initial_condition_noise_variance'][0])}"
                  f"_sw_{str(input_params['sigma'])}"
                  f"_sr_{str(input_params['reaction_sigma'])}"
                  f"_cn_{str(input_params['seed_value'][0])}"
                  f"_l_{str(input_params['location'][0][0])}"
                  f"_M3_{str(input_params['M3'])}"
                  f"_kt_{str(input_params['k_tilde'])}"
                  f"_rl_{str(input_params['rest_length'][0])}"
                  f"_wd_{str(input_params['well_depth'])}"
                #   f"_t_{str(input_params['tau'])}"
                  )

    #  + '_K_' + str(input_params['basal_k_production']) \
    # + '_well_depth_' + str(input_params['well_depth'])
    # + '_reaction_sigma_' + str(input_params['reaction_sigma'])
    return output_dir