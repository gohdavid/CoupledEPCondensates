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
