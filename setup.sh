s#!/usr/bin/env bash

# Environment and script setup for CoupledEPCondensates repository.
# For Unix systems.
# Run in the base repository folder.

# Create conda environment with Poetry
conda env create -f environment.yml -y
conda activate CoupledEPCondensates

# Install utils package and dependecies from poetry.lock file
poetry install

# Copy Gmsh compiled at engaging
module load gmsh/4.10.5
cp $(which gmsh) ${CONDA_PREFIX}/bin/
# or conda install -c conda-forge gmsh

# Define Symlinks in conda environment
# For engaging, may need to add export PATH="$HOME/miniforge3/bin:$PATH" to .bashrc
ln -s $(pwd)/utils/scripts/run_simulation.py ${CONDA_PREFIX}/bin/run-simulation
ln -s $(pwd)/utils/scripts/sweep_parameters.py ${CONDA_PREFIX}/bin/sweep-parameters
ln -s $(pwd)/utils/analysis/make_movies.py ${CONDA_PREFIX}/bin/make-movies
ln -s $(pwd)/utils/analysis/make_movie.py ${CONDA_PREFIX}/bin/make-movie
ln -s $(pwd)/utils/scripts/sweep_movies.py ${CONDA_PREFIX}/bin/sweep-movies

chmod +x  ${CONDA_PREFIX}/bin/run-simulation
chmod +x  ${CONDA_PREFIX}/bin/sweep-parameters
chmod +x  ${CONDA_PREFIX}/bin/make-movies
chmod +x  ${CONDA_PREFIX}/bin/make-movie