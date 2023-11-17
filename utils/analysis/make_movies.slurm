#!/bin/bash
#SBATCH -J MakeMovies
#SBATCH --mail-user davidgoh
#SBATCH -p sched_mit_arupc_long
#SBATCH -t 12:00:00
#SBATCH --mem-per-cpu 16000
cd "$SLURM_SUBMIT_DIR"
echo $PWD

run_program()
{
 source activate CoupledEPCondensates
 make-movies --i $input_directory --r $match_pattern --h spatial_variables.hdf5 --p input_params.txt --m movie_parameters.txt
 conda deactivate
}

run_program
