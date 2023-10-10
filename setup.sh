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

# Add symlink to bin to execute anywhere e.g., 
# run-simulation --i input_path --o output_path
script=$(pwd)/scripts/run_simulation.py 
ln -s $script /usr/local/bin/run-simulation
chmod +x /usr/local/bin/run-simulation
