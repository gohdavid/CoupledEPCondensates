# Guide: Running Older Simulations with the Current Script

This guide outlines the necessary modifications for the parameter set in the `20231120_FlowPhaseDiagramHighRes` directory.
The data from these simulations, used for Figure 1B, were generated with a previous version of the script and are now incompatible with the current code.

The incompatibility stems from three main updates: the introduction of the `model_type`, changes to the model equations that now expect Gaussian well parameters, and additional parameters required for naming output directories.

To run the old simulations, make the following additions and changes to the `input_params.txt` file:

1. **Set Model Type**. The `model_type` parameter was added to differentiate between the two and three-component (time delay) simulations. Add `model_type, 1` to specify that we are running the two-component model.

2. **Update Free Energy Model**.
The original simulations used `free_energy_type, 2`, which is now incompatible because the current `TwoComponentModel` expects `well_center` to be a variable (in `get_gaussian_function`).
Previously, `well_center` was a static class attribute.
<br>
<br>
Switch to `free_energy_type, 3` (`TwoCompDoubleWellFHCrossQuadraticDimensionlessCoupled`).
The difference is that there is now the higher order repulsion term `chiPR_tilde`.
We need to disable the new repulsion term by setting adding `chiPR_tilde, 0` to `input_params.txt`.
Note that although there is a Gaussian well in the code, we have set the `well_depth` to zero.
Hence, we are effectively simulating an untethered condensate with attraction to RNA only.

3. **Add Legacy and Unused (Dummy) Parameters**. The script will fail without several new parameters, which are used in the directory naming convention (`get_output_dir_name` in `simulation_helper.py`). Add the following with dummy values:
    1. The parameters `k_tilde`, `M3`, `rest_length`, `r_p`, and `ratio` are legacy parameters. While they must be present in the `input_params.txt` files, they are no longer used in the simulations. Originally, these parameters were used for the enhancer dynamics, but these dynamics have been removed from the finite volume simulations and is now handled by Brownian dynamics simulations. The parameters are still parsed by the scripts and used for naming directories, but because they are not used by the simulations (i.e., not used in the update steps), they can safely be set to zero (they have no effect).
    2. `tau`. This is for the three-component model's time delay, and are unused in these simulations.

To ensure compatibility, change the `free_energy_type` to `3` and add the following lines to `input_params.txt`:
```
model_type, 1.0

chiPR_tilde, 0.0
well_depth, 0.0

k_tilde, 0.0
tau, 0.0
M3, 0
r_p, (0, 0)
rest_length, (0.0, 0.0)
ratio, 1.0
```
These changes are placed in the `input_params_compatibility.txt` file.