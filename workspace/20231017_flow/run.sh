#!/usr/bin/env bash
cd /nfs/arupclab001/davidgoh/CoupledEPCondensates/workspace/20231017_flow/
sweep-parameters --s sweep_parameters.txt \
    --i input_params.txt\
    --o /nfs/arupclab001/davidgoh/CoupledEPCondensates/workspace/20231017_flow/output