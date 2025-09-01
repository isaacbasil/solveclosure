
import shutil
import subprocess
import numpy as np 
import os 
import sys
import re
import tifffile as tif
import pickle

from solve2eqclosure.utility import add_slash, check_for_existing_solutions
from solve2eqclosure.image_analysis import calculate_area_and_volume, calculate_source_terms, check_and_write_area_and_volume_total, return_x_positions, subdivide_image_using_label_map
from solve2eqclosure.openfoam_case_setup.make_blockMeshDict import make_blockMeshDict 
from solve2eqclosure.openfoam_case_setup.make_topoSetDict import make_topoSetDict
from solve2eqclosure.openfoam_case_setup.multiparticle import write_bc_file_multiparticle, write_fvOptions_file_multiparticle, write_myFunctionsDict_multiparticle, write_p_file, write_regionProperties_file, write_surface_integral_func, write_volume_integral_func, write_thermophysicalProperties_file


# ============ Inputs ==============

def solve_closure_multiparticle(case_dir, img_path, label_map_path, load_of_cmd, voxel, cbd_surface_porosity, D_s, allow_flux=True, parallelise=False, n_procs=8, run_solver=True, T_offset=1e5):

    """
    Solves the closure problem as described in [1] using OpenFOAM. 

    Args:
        case_dir (str): The path to an empty directory where the OpenFOAM case will be built.
        img_path (str): The path to the image of the electrode micrstructure in tif format. Electrolyte labelled 0, AM as 1, and CBD as 2.
        label_map_path (str): The path to the label map which identifies particle IDs. Same dimensions as the image. 
        load_of_cmd (str): The command which must be executed in your terminal to load OpenFOAM. 
        voxel (float): The voxel side length of the image in meters. 
        cbd_surface_porosity (float): The surface porosity of the CBD phase. 
        D_s (float): The diffusivity of the AM in m2.s-1 
        allow_flux (bool): Set to False for closure Option 1 (see article). 
        parallelise (bool): Set to True to solve in parallel.   
        n_procs (int): The number of processors to use if parallelisation chosen. 
        run_solver (bool): Set to false to setup the OpenFOAM case without running the solver. 
        T_offset (float): A large number to make compatible with OpenFOAM's solvers (see docs.)
        
    Returns:
        No returns. Operates on a filesystem directory. 
    """

    # correct path if slash not added at end
    case_dir = add_slash(case_dir)

    # copy necessary template files 
    cmd = f"cp -r ./src/solve2eqclosure/template_dirs/multiparticle/* {case_dir}"
    subprocess.run(["bash", "-c", cmd], check=True)

    check_for_existing_solutions(case_dir)

    # clean directory
    of_case_dir = case_dir + "openfoam_case/"
    cmd = f"{load_of_cmd} && foamListTimes -rm -case {of_case_dir}"
    subprocess.run(["bash", "-c", cmd], check=True)
    cmd = f"cd {of_case_dir} && rm -rf ../closure_data.pickle postProcessing/ process* 0/particle_* constant/polyMesh/ constant/particle_* system/particle_* system/myFunctionsDict"
    subprocess.run(["bash", "-c", cmd], check=False)

    # load tif 
    img = tif.imread(img_path)
    label_map = tif.imread(label_map_path)

    # Inactive material is ignored and treated as elec
    img[img == 51] = 0

    # subdivide tifs to find source terms
    subsections, centres, neighbour_ids = subdivide_image_using_label_map(label_map_path, img, show_subsections=False)

    x_positions_m = return_x_positions(centres, voxel)

    # initialise closure data 
    closure_data = {"particle data": {}, 
                    "times for transient data": None, 
                    "global s surface average steady": None, 
                    "global s surface average transient": None, 
                    "global s volume average final": None,
                    "total area (surface porosity included)": None, 
                    "am-elec area": None,
                    "am-cbd area (surface porosity omitted)": None,
                    "total particle volume": None,
                    "T offset": T_offset,
                    }

    # make blockmeshDict 
    blockMeshDict_path = case_dir + "/openfoam_case/system/blockMeshDict"
    make_blockMeshDict(blockMeshDict_path, img, voxel)

    # make topoSetDict 
    topoSetDict_path = case_dir + "/openfoam_case/system/topoSetDict"
    make_topoSetDict(topoSetDict_path, img, multi_particle=True, label_map=label_map)


    particle_names = [f"particle_{key}" for key in subsections.keys()]
    myFunctionsDict_path = of_case_dir + f"/system/myFunctionsDict"
    # make empty myFunctionsDict file to prevent error when running cmds
    subprocess.run(["bash", "-c", f"touch {myFunctionsDict_path}"], check=True)
    #update_control_dict(control_dict_path, particle_names)


    # Run blockMesh
    cmd = f"{load_of_cmd} && blockMesh -case {of_case_dir}"
    subprocess.run(["bash", "-c", cmd], check=True)

    # Run topoSet
    cmd = f"{load_of_cmd} && topoSet -case {of_case_dir}"
    subprocess.run(["bash", "-c", cmd], check=True)

    # splitMeshRegions
    cmd = f"{load_of_cmd} && splitMeshRegions -case {of_case_dir} -cellZonesOnly -overwrite"
    subprocess.run(["bash", "-c", cmd], check=True)

    # get rid of Elec and CBD dirs
    cmd = f"cd {of_case_dir} && rm -rf 0/Elec constant/Elec system/Elec 0/CBD constant/CBD system/CBD"
    subprocess.run(["bash", "-c", cmd], check=False)

    # write regionProperties file
    regionprops_path = of_case_dir + f"/constant/regionProperties"
    write_regionProperties_file(regionprops_path, particle_names)


    # create source terms file
    for key, subsection in subsections.items():
        
        particle_name = "particle_" + str(key)

        # write correct source terms to OF files 
        dimensional_S_vol, dimensional_bc_elec, dimensional_bc_cbd, total_particle_area, V_am = calculate_source_terms(subsection, voxel, cbd_surface_porosity, D_s)

        closure_data["particle data"][key] = {"particle surface area": total_particle_area, "particle volume": V_am, "centre x position": x_positions_m[key - 1]}

        # === files that are edited here (except p) and not be the user ===

        bc_path = of_case_dir + f"0/particle_{key}/T"
        write_bc_file_multiparticle(bc_path, particle_name, dimensional_bc_elec, dimensional_bc_cbd, neighbour_ids, T_offset, allow_flux=allow_flux)

        p_path = of_case_dir + f"/0/particle_{key}/p"
        write_p_file(p_path, particle_name)
        
        fvOptions_path = of_case_dir + f"/constant/particle_{key}/fvOptions"
        write_fvOptions_file_multiparticle(fvOptions_path, particle_name, dimensional_S_vol)

        thermoprops_path =  of_case_dir + f"/constant/particle_{key}/thermophysicalProperties"
        write_thermophysicalProperties_file(thermoprops_path, particle_name, D_s)

        for type in ["elec", "cbd", "sep"]:
            if type in neighbour_ids[key]:
                surface_int_path = of_case_dir + f"/system/{particle_name}_surfaceIntegral_{type}"
                write_surface_integral_func(surface_int_path, particle_name, type=type)

        vol_int_path = of_case_dir + f"/system/{particle_name}_volumeIntegral"
        write_volume_integral_func(vol_int_path, particle_name)

        # === files that can be edited by the user ===
        schemes_source_path = case_dir + "solver_settings/fvSchemes"
        system_path = of_case_dir + f"/system/particle_{key}/"
        cmd = f"cp {schemes_source_path} {system_path}"
        subprocess.run(["bash", "-c", cmd], check=True)

        solution_source_path = case_dir + "solver_settings/fvSolution"
        cmd = f"cp {solution_source_path} {system_path}"
        subprocess.run(["bash", "-c", cmd], check=True)

    # add postprocessing functions
    write_myFunctionsDict_multiparticle(myFunctionsDict_path, neighbour_ids)


    if parallelise:
        # make the decomposeParDict file
        decomposeParDict_path = of_case_dir + "/system/decomposeParDict"
        update_decomposeParDict_file(decomposeParDict_path, n_procs)

        for particle_name in particle_names:
            # copy the decomposeParDict file to each particle dir
            cmd = f"cp {decomposeParDict_path} {of_case_dir}/system/{particle_name}/"
            subprocess.run(["bash", "-c", cmd], check=True)

        cmd = f"{load_of_cmd} && decomposePar -case {of_case_dir} -allRegions"
        subprocess.run(["bash", "-c", cmd], check=True)

    # if create_pangea_launch_script:
    #     pangea_launch_path = of_case_dir + "/pangea_launch.sh"
    #     write_pangea_launch_script(pangea_launch_path, n_procs, multiparticle=True)


    # check area and volume, and add it to the closure data dictionary
    closure_data = check_and_write_area_and_volume_total(closure_data, img, voxel, cbd_surface_porosity)


    # ======= write particle_data file =========
    closure_data_path = case_dir + "closure_data.pickle"
    with open(closure_data_path, 'wb') as f:
        pickle.dump(closure_data, f)

    # =========== Run solver if requested =====
    if run_solver: 
        if parallelise:
            cmd = f"{load_of_cmd} && mpirun -np {n_procs} chtMultiRegionFoam -parallel -case {of_case_dir}"
        else:
            cmd = f"{load_of_cmd} && chtMultiRegionFoam -case {of_case_dir}"
        subprocess.run(["bash", "-c", cmd], check=False)

        # reconstruct is parallelised 
        if parallelise:
            cmd = f"{load_of_cmd} && reconstructPar -case {of_case_dir} -allRegions"
            subprocess.run(["bash", "-c", cmd], check=False)


