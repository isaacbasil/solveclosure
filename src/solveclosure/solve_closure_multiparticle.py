import subprocess
import os 
import tifffile as tif
import pickle
import time 

from solveclosure.utility import add_slash, check_for_existing_solutions, find_latest_openfoam_installation
from solveclosure.image_analysis import calculate_source_terms_dimensional, calculate_source_terms_dimensionless, check_and_write_area_and_volume_total, return_x_positions, subdivide_image_using_label_map
from solveclosure.openfoam_case_setup.make_blockMeshDict import make_blockMeshDict 
from solveclosure.openfoam_case_setup.make_topoSetDict import make_topoSetDict
from solveclosure.openfoam_case_setup.multiparticle import write_bc_file_multiparticle, write_fvOptions_file_multiparticle, write_myFunctionsDict_multiparticle, write_p_file, write_regionProperties_file, write_surface_integral_func, write_volume_integral_func, write_thermophysicalProperties_file, write_decomposeParDict_file, write_controlDict_file


# ============ Inputs ==============

def solve_closure_multiparticle(case_dir, img_path, label_map_path, voxel, cbd_surf_por, sep_surf_por=1.0, dimensionless=True, D_s=None, L=None, load_of_cmd=None, allow_flux=True, parallelise=False, n_procs=8, run_solver=True, T_offset=None, time_params=None):

    """
    Solves the closure problem as described in [1] using OpenFOAM. 

    Args:
        case_dir (str): The path to an empty directory where the OpenFOAM case will be built.
        img_path (str): The path to the image of the electrode micrstructure in tif format. Electrolyte labelled 0, AM as 1, and CBD as 2.
        label_map_path (str): The path to the label map which identifies particle IDs. Same dimensions as the image. 
        voxel (float): The voxel side length of the image in meters. 
        cbd_surf_por (float): The surface porosity of the CBD phase. 
        sep_surf_por (float, optional): To model the reduced reaction rate caused by particles in contact with a separator, set the separator surface porosity.
        dimensionless (bool): Set to False to solve a dimensional case. Default is True. 
        D_s (float): The diffusivity of the AM in m2.s-1. Required if solving a dimensional case.
        L (float): The lengthscale used (m) to non-dimensionalise the problem. If None, but dimensionless=True, the length of axis 0 of the image will be used.
        load_of_cmd (str): The command which must be executed in your terminal to load OpenFOAM. If not provided OpenFOAM installations will be searched for. 
        allow_flux (bool): Set to False for closure Option 2 (see article). 
        parallelise (bool): Set to True to solve in parallel.   
        n_procs (int): The number of processors to use if parallelisation chosen. 
        run_solver (bool): Set to false to setup the OpenFOAM case without running the solver. 
        T_offset (float): A large number to make compatible with OpenFOAM's solvers (see docs). Default 1e5 for dimensional and 10 for dimensionless. 
        time_params (dict, optional): A dictionary specifying time parameters for the solver, 
        with entries "T_end" (the final simulation time), "dt" (the intial time step), "write_interval" 
        (the interval at which spatial fields are written). If None, default values will be used.
        
    Returns:
        No returns. Operates on a filesystem directory. 
    """

    # check inputs 
    if not dimensionless and D_s is None:
        raise ValueError("\nD_s must be provided for dimensional case.")
    
    if dimensionless:
        D_s = 1
    
    if T_offset is None:
        if dimensionless:
            T_offset = 10
        else:
            T_offset = 1e5
    
    # look for OF 
    if load_of_cmd is None:
        load_of_cmd = find_latest_openfoam_installation()
        
    # correct path if slash not added at end
    case_dir = add_slash(case_dir)

    check_for_existing_solutions(case_dir)

    start_time = time.time()
    
    print("Copying template files for OpenFOAM case.")
    # copy necessary template files 
    template_path = os.path.join(os.path.dirname(__file__), "templates/multiparticle/")
    cmd = f"cp -r {template_path}* {case_dir}"
    subprocess.run(["bash", "-c", cmd], check=True)

    # write controlDict file
    controlDict_path = case_dir + "/openfoam_case/system/controlDict"
    write_controlDict_file(controlDict_path, dimensionless, time_params)

    # clean directory
    of_case_dir = case_dir + "openfoam_case/"
    cmd = f"{load_of_cmd} && foamListTimes -rm -case {of_case_dir}"
    subprocess.run(["bash", "-c", cmd], check=True)
    cmd = f"cd {of_case_dir} && rm -rf ../closure_data.pickle postProcessing/ process* 0/particle_* constant/polyMesh/ constant/particle_* system/particle_* system/myFunctionsDict log*"
    subprocess.run(["bash", "-c", cmd], check=False)

    # load tif 
    print("Analysing image.")
    img = tif.imread(img_path)
    label_map = tif.imread(label_map_path)

    if dimensionless and L is None:
        print("\nLengthscale not provided for dimensionless case. Setting to length of the image's axis 0 by default.")
        L = img.shape[0] * voxel

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
                    "dimensionless": dimensionless,
                    }

    
    print("\nGenerating files for OpenFOAM case.")
    # make blockmeshDict 
    blockMeshDict_path = case_dir + "/openfoam_case/system/blockMeshDict"
    make_blockMeshDict(blockMeshDict_path, img, voxel, dimensionless, L)

    # make topoSetDict 
    topoSetDict_path = case_dir + "/openfoam_case/system/topoSetDict"
    make_topoSetDict(topoSetDict_path, img, multi_particle=True, label_map=label_map)


    particle_names = [f"particle_{key}" for key in subsections.keys()]
    myFunctionsDict_path = of_case_dir + f"/system/myFunctionsDict"
    # make empty myFunctionsDict file to prevent error when running cmds
    subprocess.run(["bash", "-c", f"touch {myFunctionsDict_path}"], check=True)

    print("Running OpenFOAM commands: blockMesh, topoSet, splitMeshRegions.")
    # Run blockMesh
    cmd = f"{load_of_cmd} && blockMesh -case {of_case_dir} > {of_case_dir}log.blockMesh 2>&1"
    subprocess.run(["bash", "-c", cmd], check=True)

    # Run topoSet
    cmd = f"{load_of_cmd} && topoSet -case {of_case_dir} > {of_case_dir}log.topoSet 2>&1"
    subprocess.run(["bash", "-c", cmd], check=True)

    # splitMeshRegions
    cmd = f"{load_of_cmd} && splitMeshRegions -case {of_case_dir} -cellZonesOnly -overwrite > {of_case_dir}log.splitMeshRegions 2>&1"
    subprocess.run(["bash", "-c", cmd], check=True)

    # get rid of Elec and CBD dirs
    cmd = f"cd {of_case_dir} && rm -rf 0/Elec constant/Elec system/Elec 0/CBD constant/CBD system/CBD"
    subprocess.run(["bash", "-c", cmd], check=False)

    # write regionProperties file
    regionprops_path = of_case_dir + f"/constant/regionProperties"
    write_regionProperties_file(regionprops_path, particle_names)


    print("Calculating and writing source terms and BCs for each particle.")
    # create source terms file
    for key, subsection in subsections.items():
        
        particle_name = "particle_" + str(key)

        # write correct source terms to OF files 
        if dimensionless:
            S_vol, bc_source_elec, bc_source_cbd, total_particle_area, V_am = calculate_source_terms_dimensionless(subsection, voxel, cbd_surf_por, L)
        else:
            S_vol, bc_source_elec, bc_source_cbd, total_particle_area, V_am = calculate_source_terms_dimensional(subsection, voxel, cbd_surf_por, D_s)

        closure_data["particle data"][key] = {"particle surface area": total_particle_area, "particle volume": V_am, "centre x position": x_positions_m[key - 1]}

        # === files that are edited here (except p) and not be the user ===

        bc_path = of_case_dir + f"0/particle_{key}/T"
        write_bc_file_multiparticle(bc_path, particle_name, bc_source_elec, bc_source_cbd, neighbour_ids, T_offset, allow_flux=allow_flux)

        p_path = of_case_dir + f"/0/particle_{key}/p"
        write_p_file(p_path, particle_name)
        
        fvOptions_path = of_case_dir + f"/constant/particle_{key}/fvOptions"
        write_fvOptions_file_multiparticle(fvOptions_path, particle_name, S_vol)

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
        print("Decomposing for parallel run.")
        # make the decomposeParDict file
        decomposeParDict_path = of_case_dir + "/system/decomposeParDict"
        write_decomposeParDict_file(decomposeParDict_path, n_procs)

        for particle_name in particle_names:
            # copy the decomposeParDict file to each particle dir
            cmd = f"cp {decomposeParDict_path} {of_case_dir}/system/{particle_name}/"
            subprocess.run(["bash", "-c", cmd], check=True)

        cmd = f"{load_of_cmd} && decomposePar -case {of_case_dir} -allRegions > {of_case_dir}log.decomposePar 2>&1"
        subprocess.run(["bash", "-c", cmd], check=True)


    # check area and volume, and add it to the closure data dictionary
    closure_data = check_and_write_area_and_volume_total(closure_data, img, voxel, cbd_surf_por)


    # ======= write particle_data file =========
    closure_data_path = case_dir + "closure_data.pickle"
    with open(closure_data_path, 'wb') as f:
        pickle.dump(closure_data, f)

    # =========== Run solver if requested =====
    if run_solver: 
        print("Running solver.")
        if parallelise:
            cmd = f"{load_of_cmd} && mpirun -np {n_procs} chtMultiRegionFoam -parallel -case {of_case_dir} > {of_case_dir}log.solver 2>&1"
        else:
            cmd = f"{load_of_cmd} && chtMultiRegionFoam -case {of_case_dir} > {of_case_dir}log.solver 2>&1"
        subprocess.run(["bash", "-c", cmd], check=False)

        # reconstruct is parallelised 
        if parallelise:
            print("Reconstructing results.")
            cmd = f"{load_of_cmd} && reconstructPar -case {of_case_dir} -allRegions > {of_case_dir}log.reconstructPar 2>&1"
            subprocess.run(["bash", "-c", cmd], check=False)

        from solveclosure.process_closure_results import process_closure_results
        print("Processing closure results.")
        process_closure_results(case_dir, cbd_surf_por, sep_surf_por, dimensionless, L=L, write=True, multiparticle=True)  

    end_time = time.time()
    print("\nThe total run time was ", round(end_time - start_time, 1), " seconds.")      


