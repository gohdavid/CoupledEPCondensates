# Finite volume simulations of condensates and localized RNA transcription

This package can be used to perform finite volume simulations of a condensate responding to localized RNA transcription. The condensate can be coupled to an attractive Gaussian potential and RNA transcription can respond to the concentration of protein after a time delay.

Use `setup.sh` to set up the Conda environment.

Gmsh is installed externally and loaded with `module load gmsh/4.10.5`. An alternative is to use `pip install gmsh` on the Conda environment.

To run the simulations:

1. Create an input parameter text file under /inputs to define your system. An example file is provided. The code documentation has information on what each parameter in this file means.
2. Run simulations on the command line using: ``python run_simulation.py --i path/to/input/parameter/file --o path/to/output/directory/to/write/simulation/data``
3. Make movies of your simulations using the script analysis/make_movies.py
4. To make movies, run the following command on the command line: ``python make_movies.py --i path/to/directory/containing/simulation/data``

If you would like to sweep or iterate over certain values of parameters in the input parameter file, then specify the parameter names and list of values in the sweep_parameters.txt file inside the /inputs directory. Then use the command:
`` python sweep_parameters.py --s path/to/sweep_parameters.txt --i ../path_to_input/parameter/file --o path/to/directory/containing/simulation/data ``. Note that for the above to work, you need to have a bash script named run_simulation.slurm of the form described under the /scripts directory.

## Note on legacy parameters

The parameters `k_tilde`, `M3`, `rest_length`, `r_p`, and `ratio` are legacy parameters. While they must be present in the `input_params.txt` files, they are no longer used in the simulations. Originally, these parameters were used for the enhancer dynamics, but these dynamics have been removed from the finite volume simulations and is now handled by Brownian dynamics simulations. The parameters are still parsed by the scripts and used for naming directories, but because they are not used by the simulations (i.e., not used in the update steps), they can safely be set to zero (they have no effect).

## Jupyter Notebooks
| Figure | Notebook |
| - | - |
| Fig. 1B | `FVM/workspace/01_Analysis/Fig_1B.ipynb` and `FVM/workspace/01_Analysis/Fig_1B_I-II-III.ipynb` |
| Fig. 2E | `FVM/workspace/04_Analysis/Fig_2E.ipynb` |
| Fig. 3B | `FVM/workspace/05_Analysis/Fig_3B-3C.ipynb` |
| Fig. 3C | `FVM/workspace/05_Analysis/Fig_3B-3C.ipynb` |
| Fig. 3D | `FVM/workspace/05_Analysis/Fig_3D.ipynb` |
| Fig. 4C | `FVM/workspace/05_Analysis/Fig_4C-4D.ipynb` |
| Fig. 4D | `FVM/workspace/05_Analysis/Fig_4C-4D.ipynb` |
| Fig. S1 | `FVM/workspace/01_Analysis/Fig_S1-S2-S3.ipynb` |
| Fig. S2 | `FVM/workspace/01_Analysis/Fig_S1-S2-S3.ipynb` |
| Fig. S3 | `FVM/workspace/01_Analysis/Fig_S1-S2-S3.ipynb` |
| Fig. S5 | `FVM/workspace/00_Misc/Fig_S5-S15-S16-S17.ipynb` |
| Fig. S14 | `FVM/Fig_S14.ipynb` |
| Fig. S15 | `FVM/workspace/00_Misc/Fig_S5-S15-S16-S17.ipynb` |
| Fig. S16 | `FVM/workspace/00_Misc/Fig_S5-S15-S16-S17.ipynb` |
| Fig. S17 | `FVM/workspace/00_Misc/Fig_S5-S15-S16-S17.ipynb`|
| Fig. S18 | `FVM/workspace/05_Analysis/Fig_S18-S19-S20.ipynb` |
| Fig. S19 | `FVM/workspace/05_Analysis/Fig_S18-S19-S20.ipynb` |
| Fig. S20 | `FVM/workspace/05_Analysis/Fig_S18-S19-S20.ipynb` |
| Fig. S21 | `FVM/workspace/05_Analysis/Fig_S21.ipynb` |