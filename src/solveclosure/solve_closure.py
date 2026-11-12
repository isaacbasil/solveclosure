import subprocess
import os 
import tifffile as tif
import pickle
import time 
import warnings

from solveclosure.utility import add_slash, check_for_existing_solutions, find_latest_openfoam_installation, check_image_labels, check_surface_porosities, merge_postprocessing_time_folders, save_surface_average_plot
from solveclosure.image_analysis import calculate_source_terms_dimensional, calculate_source_terms_dimensionless, check_and_write_area_and_volume_total, return_x_positions, subdivide_image_using_label_map
from solveclosure.openfoam_case_setup import make_blockMeshDict, make_topoSetDict, write_bc_file, write_fvOptions_file, write_myFunctionsDict, write_p_file, write_regionProperties_file, write_surface_integral_func, write_volume_integral_func, write_thermophysicalProperties_file, write_decomposeParDict_file, write_controlDict_file


# relative range (max - min) of the global surface average over the last half of the run below which it counts as steady
STEADY_STATE_RTOL = 1e-3

# ============ Inputs ==============

def solve_closure(case_dir, img_path, label_map_path, voxel, *, cbd_surf_por=None, sep_surf_por=None, dimensionless=True, D_s=None, L=None, load_of_cmd=None, allow_flux=True, parallelise=False, n_procs=8, run_solver=True, T_offset=None, end_time=None, write_interval=None, continue_to_steady_state=True, max_end_time=None, save_plot=True):

    """
    Solves the closure problem as described in [1] using OpenFOAM. 

    Args:
        case_dir (str): The path to an empty directory where the OpenFOAM case will be built.
        img_path (str): The path to the image of the electrode microstructure in tif format. Electrolyte labelled 0, AM as 1, CBD as 2, separator as 3 and inactive material as 51. Inactive material blocks the AM surface it touches (no reaction and no flux).
        label_map_path (str): The path to the label map which identifies particle IDs. Same dimensions as the image. 
        voxel (float): The voxel side length of the image in meters. 
        cbd_surf_por (float, optional): The surface porosity of the CBD, applied where AM touches CBD voxels (label 2).
            Must be given if the image contains CBD. If the image contains no CBD it has no effect (a warning is shown if it is given), and None is saved if it is not given.
        sep_surf_por (float, optional): The surface porosity of the separator, applied where AM touches separator voxels (label 3).
            Must be given if the image contains separator. If the image contains no separator it has no effect (a warning is shown if it is given), and None is saved if it is not given.
        dimensionless (bool): Set to False to solve a dimensional case. Default is True. 
        D_s (float): The diffusivity of the AM in m2.s-1. Required if solving a dimensional case.
        L (float): The lengthscale used (m) to non-dimensionalise the problem. If None, but dimensionless=True, the length of axis 0 of the image will be used.
        load_of_cmd (str): The command which must be executed in your terminal to load OpenFOAM. If not provided OpenFOAM installations will be searched for. 
        allow_flux (bool): Set to False for closure Option 2 (see article). 
        parallelise (bool): Set to True to solve in parallel.   
        n_procs (int): The number of processors to use if parallelisation chosen. 
        run_solver (bool): Set to false to setup the OpenFOAM case without running the solver. 
        T_offset (float): A large number to make compatible with OpenFOAM's solvers (see docs). Default 1e5 for dimensional and 10 for dimensionless. 
        end_time (float, optional): The simulation end time: dimensionless time for a dimensionless case, seconds for a dimensional case.
            The solver must run long enough to reach steady state. Default 0.25 for a dimensionless case, and (image length along axis 0)^2 / (4 D_s)
            for a dimensional case, which is the same physical time. If steady state is not reached by end_time and continue_to_steady_state
            is True, the solver is continued from where it stopped, doubling the end time each time, until steady state or max_end_time is reached.
        write_interval (float, optional): How often the 3D fields are written for viewing, for example in ParaView, in the same units as end_time.
            It does not affect the results. Default end_time / 4, which is updated when the solver is continued.
        continue_to_steady_state (bool, optional): Set to False to stop at end_time even if steady state has not been reached.
            A warning is shown if it has not. Default True.
        max_end_time (float, optional): The longest the solver may be continued to if steady state is not reached. Default 16 * end_time
            (up to four continuations). Ignored if continue_to_steady_state is False. If steady state is still not reached, a warning is shown.
        save_plot (bool, optional): Save a png of the corrected global surface average of the closure variable against time
            (``surface_average.png`` in case_dir), once the results have been processed. Ignored if run_solver is False. Default True.
        
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
    
    if end_time is not None and end_time <= 0:
        raise ValueError("end_time must be positive.")
    if write_interval is not None and write_interval <= 0:
        raise ValueError("write_interval must be positive.")

    start_time = time.time()

    # load tif
    print("Analysing image.")
    img = tif.imread(img_path)
    label_map = tif.imread(label_map_path)
    check_image_labels(img, label_map)
    # surface porosities are required for the phases in the image, and None for those that are not (unless given)
    cbd_surf_por, sep_surf_por = check_surface_porosities(img, cbd_surf_por, sep_surf_por)
    # the area and source term calculations need numbers: a phase that is not in the image has no area, so 0 has no effect
    cbd_por_calc = 0.0 if cbd_surf_por is None else cbd_surf_por
    sep_por_calc = 0.0 if sep_surf_por is None else sep_surf_por

    # look for OF 
    if load_of_cmd is None:
        load_of_cmd = find_latest_openfoam_installation()
        
    # correct path if slash not added at end
    case_dir = add_slash(case_dir)

    check_for_existing_solutions(case_dir)

    if dimensionless and L is None:
        print("\nLengthscale not provided for dimensionless case. Setting to length of the image's axis 0 by default.")
        L = img.shape[0] * voxel

    # simulation time: t_hat = 0.25 for a dimensionless case, the same physical time (image length^2 / (4 D_s)) for a dimensional case.
    # Cases that need longer are continued automatically (see continue_to_steady_state).
    if end_time is None:
        end_time = 0.25 if dimensionless else (img.shape[0] * voxel) ** 2 / (4 * D_s)
    scale_write_interval = write_interval is None  # default: keep it at a quarter of the (possibly continued) end time
    if write_interval is None:
        write_interval = end_time / 4
    if max_end_time is None:
        max_end_time = 16 * end_time
    elif max_end_time < end_time:
        raise ValueError("max_end_time must not be smaller than end_time.")
    
    print("Copying template files for OpenFOAM case.")
    # copy necessary template files 
    template_path = os.path.join(os.path.dirname(__file__), "templates/")
    cmd = f"cp -r {template_path}openfoam_case {template_path}solver_settings {case_dir}"
    subprocess.run(["bash", "-c", cmd], check=True)

    # write controlDict file
    controlDict_path = case_dir + "/openfoam_case/system/controlDict"
    write_controlDict_file(controlDict_path, dimensionless, end_time, write_interval)

    # clean directory
    of_case_dir = case_dir + "openfoam_case/"
    cmd = f"{load_of_cmd} && foamListTimes -rm -case {of_case_dir}"
    subprocess.run(["bash", "-c", cmd], check=True)
    cmd = f"cd {of_case_dir} && rm -rf ../closure_data.pickle ../surface_average.png postProcessing/ process* 0/particle_* constant/polyMesh/ constant/particle_* system/particle_* system/myFunctionsDict log*"
    subprocess.run(["bash", "-c", cmd], check=False)

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
                    "am-sep area (surface porosity omitted)": None,
                    "total particle volume": None,
                    "T offset": T_offset,
                    "dimensionless": dimensionless,
                    "L": L, # lengthscale (m) used to non-dimensionalise; None for a dimensional case
                    "voxel": voxel, # voxel side length (m)
                    "cbd surface porosity": cbd_surf_por,
                    "sep surface porosity": sep_surf_por,
                    "end time": end_time,
                    "write interval": write_interval,
                    "continue to steady state": continue_to_steady_state,
                    "max end time": max_end_time,
                    "continuations": 0, # number of times the solver was continued to reach steady state
                    }

    
    print("\nGenerating files for OpenFOAM case.")
    # make blockmeshDict 
    blockMeshDict_path = case_dir + "/openfoam_case/system/blockMeshDict"
    make_blockMeshDict(blockMeshDict_path, img, voxel, dimensionless, L)

    # make topoSetDict 
    topoSetDict_path = case_dir + "/openfoam_case/system/topoSetDict"
    make_topoSetDict(topoSetDict_path, img, label_map)


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

    # get rid of Elec, CBD, Sep and Inactive dirs
    cmd = f"cd {of_case_dir} && rm -rf 0/Elec constant/Elec system/Elec 0/CBD constant/CBD system/CBD 0/Sep constant/Sep system/Sep 0/Inactive constant/Inactive system/Inactive"
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
            S_vol, bc_source_elec, bc_source_cbd, bc_source_sep, total_particle_area, V_am = calculate_source_terms_dimensionless(subsection, voxel, cbd_por_calc, sep_por_calc, L)
        else:
            S_vol, bc_source_elec, bc_source_cbd, bc_source_sep, total_particle_area, V_am = calculate_source_terms_dimensional(subsection, voxel, cbd_por_calc, sep_por_calc, D_s)

        closure_data["particle data"][key] = {"particle surface area": total_particle_area, "particle volume": V_am, "centre x position": x_positions_m[key - 1]}

        # === files that are edited here (except p) and not be the user ===

        bc_path = of_case_dir + f"0/particle_{key}/T"
        write_bc_file(bc_path, particle_name, bc_source_elec, bc_source_cbd, bc_source_sep, neighbour_ids[key], T_offset, allow_flux=allow_flux)

        p_path = of_case_dir + f"/0/particle_{key}/p"
        write_p_file(p_path, particle_name)
        
        fvOptions_path = of_case_dir + f"/constant/particle_{key}/fvOptions"
        write_fvOptions_file(fvOptions_path, particle_name, S_vol)

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
    write_myFunctionsDict(myFunctionsDict_path, neighbour_ids)


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
    closure_data = check_and_write_area_and_volume_total(closure_data, img, voxel, cbd_por_calc, sep_por_calc)


    # ======= write particle_data file =========
    closure_data_path = case_dir + "closure_data.pickle"
    with open(closure_data_path, 'wb') as f:
        pickle.dump(closure_data, f)

    # =========== Run solver if requested =====
    if run_solver: 
        from solveclosure.process_closure_results import process_closure_results, check_steady_state

        def run_openfoam(log_suffix=""):
            if parallelise:
                cmd = f"{load_of_cmd} && mpirun -np {n_procs} chtMultiRegionFoam -parallel -case {of_case_dir} > {of_case_dir}log.solver{log_suffix} 2>&1"
            else:
                cmd = f"{load_of_cmd} && chtMultiRegionFoam -case {of_case_dir} > {of_case_dir}log.solver{log_suffix} 2>&1"
            subprocess.run(["bash", "-c", cmd], check=False)

            # reconstruct if parallelised (only the times that are not reconstructed yet)
            if parallelise:
                print("Reconstructing results.")
                cmd = f"{load_of_cmd} && reconstructPar -case {of_case_dir} -allRegions -newTimes > {of_case_dir}log.reconstructPar{log_suffix} 2>&1"
                subprocess.run(["bash", "-c", cmd], check=False)

        def process_and_check():
            # process quietly; returns True if the global surface average reached steady state
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", UserWarning)
                process_closure_results(case_dir, write=True)
            with open(closure_data_path, 'rb') as f:
                data = pickle.load(f)
            relative_range = check_steady_state_quietly(data["times for transient data"], data["global s surface average transient"])
            return relative_range <= STEADY_STATE_RTOL

        def check_steady_state_quietly(t, s):
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", UserWarning)
                return check_steady_state(t, s, rtol=STEADY_STATE_RTOL)

        print("Running solver.")
        run_openfoam()
        print("Processing closure results.")
        steady = process_and_check()

        current_end_time = end_time
        continuations = 0
        while continue_to_steady_state and not steady and current_end_time * 2 <= max_end_time * (1 + 1e-12):
            current_end_time *= 2
            continuations += 1
            if scale_write_interval:
                write_interval = current_end_time / 4
            print(f"\nSteady state not reached. Continuing the solver to an end time of {current_end_time:g}.")
            write_controlDict_file(controlDict_path, dimensionless, current_end_time, write_interval, start_from="latestTime")
            run_openfoam(log_suffix=f"_continued_{continuations}")
            merge_postprocessing_time_folders(of_case_dir)
            steady = process_and_check()

        # record the time the solver actually reached
        with open(closure_data_path, 'rb') as f:
            data = pickle.load(f)
        data["end time"] = current_end_time
        data["write interval"] = write_interval
        data["continuations"] = continuations
        with open(closure_data_path, 'wb') as f:
            pickle.dump(data, f)

        # report the final state (warns if steady state was still not reached)
        check_steady_state(data["times for transient data"], data["global s surface average transient"], rtol=STEADY_STATE_RTOL)

        if save_plot:
            plot_path = case_dir + "surface_average.png"
            save_surface_average_plot(data, plot_path)
            print(f"Saved a plot of the surface average against time to {plot_path}")

    wall_end_time = time.time()
    print("\nThe total run time was ", round(wall_end_time - start_time, 1), " seconds.")


def solve_closure_multiparticle(*args, **kwargs):
    """
    Deprecated alias of :func:`solve_closure`.

    .. deprecated:: 0.2.0
        Use :func:`solveclosure.solve_closure` instead. This alias will be removed in a future release.
    """
    warnings.warn(
        "solve_closure_multiparticle has been renamed to solve_closure and will be removed in a future release.",
        DeprecationWarning,
        stacklevel=2,
    )
    return solve_closure(*args, **kwargs)
