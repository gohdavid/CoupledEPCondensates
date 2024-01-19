#!/bin/bash
#SBATCH -J CoupledEPCondensates
#SBATCH --mail-user davidgoh
#SBATCH -p sched_mit_arupc_long
#SBATCH -t 2:00:00
#SBATCH --mem-per-cpu 4000


movie()
{
    source activate CoupledEPCondensates
    make-movie --i $input
    conda deactivate
}

movie