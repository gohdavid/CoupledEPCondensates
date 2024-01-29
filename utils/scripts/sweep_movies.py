#!/usr/bin/env python
"""
Script to sweep through different parameters in an input_parameters file over values defined in a sweep_parameters file
"""

import os
from datetime import datetime
import itertools
import argparse
import utils.file_operations as file_operations
import textwrap

if __name__ == "__main__":
    """This script generates a separate input_parameter file for each parameter in sweep_parameters file
    """

    # Read command line arguments that describe file containing input parameters and folder to output simulation results
    parser = argparse.ArgumentParser(description='sweep_parameter file, input_parameter file, \
                                                  and output directory for simulation jobs are command line arguments')
    parser.add_argument('--s', help="Name of sweep_parameter file", required=True)
    parser.add_argument('--i', help="Name of input_parameter file", required=True)
    parser.add_argument('--o', help="Name of output directory", required=True)
    args = parser.parse_args()

    input_parameter_file = args.i
    sweep_parameter_file = args.s
    output_directory = args.o

    # Read input parameters from file
    input_parameters = file_operations.input_parse(filename=input_parameter_file)
    print('Successfully parsed input parameters ...')

    # Read parameters to sweep in the sweep_parameters file
    sweep_parameters = file_operations.input_parse(filename=sweep_parameter_file)
    print('Successfully parsed sweep parameters ...')

    sweep_parameter_names = []
    sweep_parameter_values = []
    for key, values in sweep_parameters.items():
        sweep_parameter_names.append(key)
        sweep_parameter_values.append(values)

    # Create a bunch of input_parameter files by sweeping across parameter values in sweep_parameters
    date_time = datetime.now()
    if not os.path.exists(os.path.join(output_directory, 'parameter_sweep_log')):
        os.mkdir(os.path.join(output_directory, 'parameter_sweep_log'))
    target_directory = os.path.join(output_directory, 'parameter_sweep_log', date_time.strftime('%d_%m_%Y_%H_%M_%S'))
    os.mkdir(target_directory)

    file_counter = 0
    for parameter_combinations in list(itertools.product(*sweep_parameter_values)):
        for parameter_counter in range(len(sweep_parameter_names)):
            input_parameters[sweep_parameter_names[parameter_counter]] = parameter_combinations[parameter_counter]
        input_parameter_file_name_during_sweep = os.path.join(target_directory,
                                                              'input_parameters_{}.txt'.format(file_counter))
        # Write parameter files
        file_operations.write_input_params_from_dict(input_parameters=input_parameters,
                                                     target_filename=input_parameter_file_name_during_sweep)
        # Submit job using this parameter file
        # Write a default run_simulation.slurm file if it does not exist in the
        # repository
        run_simulation_slurm = """\
        #!/bin/bash
        #SBATCH -J CoupledEPCondensates
        #SBATCH --mail-user davidgoh
        #SBATCH -p sched_mit_arupc,sched_mit_arupc_long
        #SBATCH -t 3:00:00
        #SBATCH --mem-per-cpu 4000
        cd "$SLURM_SUBMIT_DIR"
        echo $PWD

        movie()
        {
            source activate CoupledEPCondensates
            output_folder=$(python -c "from utils.simulation_helper import get_output_dir_name as outname; from utils.file_operations import input_parse;  print(outname(input_parse('$input_file')))")
            make-movie --i $output_folder
            conda deactivate
            echo "DONE"
        }
        movie
        """
        run_simulation_slurm = textwrap.dedent(run_simulation_slurm)
        with open("run_simulation.slurm","w") as fhandle:
            fhandle.write(run_simulation_slurm)

        os.system('sbatch --export=input_file={},out_folder={} run_simulation.slurm'
                    .format(input_parameter_file_name_during_sweep, output_directory))

        file_counter = file_counter + 1
