#!/usr/bin/env bash
#
# Environment and script setup for CoupledEPCondensates repository.
# For Unix systems.
# Run in the base repository folder.

# Create conda environment with Poetry
# conda env create -f environment.yml -y
# conda activate CoupledEPCondensates

# Install utils package and dependecies from poetry.lock file
# poetry install

# Copy Gmsh compiled at engaging
# module load gmsh/4.10.5
# cp $(which gmsh) ${CONDA_PREFIX}/bin/

# symlinks
ln -s $(pwd)/utils/scripts/run_simulation.py ${CONDA_PREFIX}/bin/run-simulation
ln -s $(pwd)/utils/scripts/sweep_parameters.py ${CONDA_PREFIX}/bin/sweep-parameter

chmod +x  ${CONDA_PREFIX}/bin/run-simulation
chmod +x  ${CONDA_PREFIX}/bin/sweep-parameter