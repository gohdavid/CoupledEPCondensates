#!/usr/bin/env bash

#SBATCH -J MakeMovies
#SBATCH --mail-user davidgoh
#SBATCH -p sched_mit_arupc_long
#SBATCH -t 0:20:00

source ~/.bashrc
mamba activate CoupledEPCondensates
echo $folder
/nfs/arupclab001/davidgoh/CoupledEPCondensates/utils/analysis/condensate_property_plot.py -i $folder