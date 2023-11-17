#!/bin/bash
#SBATCH -J CoupledEPCondensates
#SBATCH --mail-user davidgoh
#SBATCH -p sched_mit_arupc,sched_mit_arupc_long
#SBATCH -t 48:00:00
#SBATCH --mem-per-cpu 4000
cd "$SLURM_SUBMIT_DIR"
echo $PWD

stage_parameters()
{
    cp $input_file input_parameters_$SLURM_JOBID.txt
}

run_program()
{
    source activate CoupledEPCondensates
    run-simulation --i $input_file --o $out_folder
    conda deactivate
}

cleanup_files()
{
    rm input_parameters_$SLURM_JOBID.txt
}

movie()
{
    source activate CoupledEPCondensates
    make-movie --i $out_folder
    conda deactivate
    echo "DONE"
}
stage_parameters
run_program
cleanup_files
movie
