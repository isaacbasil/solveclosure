#!/bin/bash
#SBATCH --partition=name_of_machine
#SBATCH --ntasks=number_of_procs
#SBATCH --cpus-per-task=1
#SBATCH --nodes=1
#SBATCH --comment="OpenFOAM"
#SBATCH --exclusive

#module purge
export OMP_NUM_THREADS=1

source /path/to/your/venv/bin/activate

python3 /path/to/your/python/launch/script.py