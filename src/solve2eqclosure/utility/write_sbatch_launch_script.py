import os
    
def write_sbatch_launch_script(file_path, n_procs, multiparticle=True):
    """
    Writes a launch script for a slurm system.

    Args:
        file_path (str): The absolute path to the sbatch launch file. 
        n_procs (int): The number of processors used for parallelisation.
        multiparticle (bool): Set to True for a multiparticle case.

    Returns:
    """

    content = f"""
#!/bin/bash
#SBATCH --partition=name_of_machine
#SBATCH --ntasks={n_procs}
#SBATCH --cpus-per-task=1
#SBATCH --nodes=1
#SBATCH --comment="OpenFOAM"

#module purge
export OMP_NUM_THREADS=1

module load openfoam/2006_220610

"""
    if multiparticle:
        solver = "chtMultiRegionFoam"
    else:
        solver = "laplacianFoam"

    if n_procs > 1:
        content += f"""
for d in processor*; do
    (cd "$d" && foamListTimes -rm)
done

mpirun -np {n_procs} {solver} -parallel > log.solver 2>&1

        """

    else:
        content += "foamListTimes -rm \n"
        content += f"{solver} > log.solver 2>&1 \n"

    
    with open(file_path, 'w') as f:
        f.write(content)

    os.chmod(file_path, 0o755)  # Make the script executable