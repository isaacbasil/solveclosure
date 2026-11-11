import numpy as np 
import pickle
import subprocess
import warnings
from solveclosure.utility import load_openfoam_data


def process_closure_results(case_dir, write=True):
    """
    Processes the closure results from a solved OpenFOAM case, and writes them to the closure_data dictionary. 

    The case settings (dimensionless, L and the CBD and separator surface porosities) are read from
    closure_data.pickle, where solve_closure saved them, so the results always match the solved case.
    
    Args:
        case_dir (str): The path to the directory where the OpenFOAM case was solved.
        write (bool): Set to False to not write results to the closure_dict, but only print them.

    Returns: 
        closure_data (dict): The dictionary containing the closure results and other image data.
    """

    closure_data_dict_path = case_dir + "closure_data.pickle"

    # make a backup 
    subprocess.run(["bash", "-c", f"cd {case_dir} && cp closure_data.pickle closure_data_backup.pickle"], check=False)

    with open(closure_data_dict_path, 'rb') as closure_data_file:
        closure_data = pickle.load(closure_data_file)

    # case settings saved by solve_closure
    required = ["T offset", "dimensionless", "L", "cbd surface porosity", "sep surface porosity"]
    missing = [key for key in required if key not in closure_data]
    if missing:
        raise KeyError(f"closure_data.pickle is missing {missing}. Cases set up before solveclosure 0.2.0 do not save these settings; "
                       "see 'Reprocessing results' in the user guide for how to add them.")

    offset = closure_data["T offset"]
    dimensionless = closure_data["dimensionless"]
    L = closure_data["L"]
    cbd_surf_por = closure_data["cbd surface porosity"]
    sep_surf_por = closure_data["sep surface porosity"]
    closure_data["method"] = "multiparticle" # kept so existing results files and scripts that read this key still work

    t_initiated = False

    no_file_found = {"elec" : 0, "cbd" : 0, "sep" : 0}

    surf_por = {"elec" : 1, "cbd" : cbd_surf_por, "sep" : sep_surf_por}

    for key in closure_data["particle data"].keys():
        
        particle_initiated = False

        for type in ["elec", "cbd", "sep"]:

            s_surf_int_path = case_dir + f"/openfoam_case/postProcessing/particle_{key}/particle_{key}_surfaceIntegral_{type}/0/surfaceFieldValue.dat"

            
            try:
                t, s_surf_int_i = load_openfoam_data(s_surf_int_path)
            except FileNotFoundError:
                no_file_found[type] += 1
                continue
            
            if len(s_surf_int_i) == 0:
                print(f"\n Although a surface integral file existed for particle {key} with type {type} it is empty \n")
                continue 
            
            if not t_initiated:
                global_sum_s_surf_int_transient = np.zeros(len(t))
                global_sum_s_vol_int_transient = np.zeros(len(t))
                closure_data["times for transient data"] = t
                t_initiated = True

            if not particle_initiated:
                closure_data["particle data"][key]["s surf int transient"] = np.zeros(len(closure_data["times for transient data"]))
                particle_initiated = True

            for t_idx in range(len(closure_data["times for transient data"])):
                global_sum_s_surf_int_transient[t_idx] += surf_por[type] * s_surf_int_i[t_idx]
                closure_data["particle data"][key]["s surf int transient"][t_idx] += surf_por[type] * s_surf_int_i[t_idx]

        # get volume integral to calculate volume average 
        s_vol_int_path = case_dir + f"/openfoam_case/postProcessing/particle_{key}/particle_{key}_volumeIntegral/0/volFieldValue.dat"

        try:
            t_vol, s_vol_int_i = load_openfoam_data(s_vol_int_path)
        except FileNotFoundError:
            print(f"\n No file found for the volume integral/average for particle {key}")
            continue  

        for t_idx in range(len(closure_data["times for transient data"])):
            global_sum_s_vol_int_transient[t_idx] += s_vol_int_i[t_idx]
 

    for type in ["elec", "cbd", "sep"]:
        print(f"\n{no_file_found[type]} particles did not have an AM-{type} surface integral file.")

    
    # divde by A
    if dimensionless:
        total_A = closure_data["total area (surface porosity included)"] / L**2
        total_particle_V = closure_data["total particle volume"] / L**3
    else:
        total_A = closure_data["total area (surface porosity included)"]
        total_particle_V = closure_data["total particle volume"]

    global_s_surf_ave_transient = global_sum_s_surf_int_transient / total_A

    s_vol_ave_transient = global_sum_s_vol_int_transient / total_particle_V

    global_s_surf_ave_ss = global_s_surf_ave_transient[-1]

    s_vol_ave_final = s_vol_ave_transient[-1]

    # subtract the T offset added to keep OpenFOAM's temperature positive
    global_s_surf_ave_ss = global_s_surf_ave_ss - offset
    global_s_surf_ave_transient = global_s_surf_ave_transient - offset
    s_vol_ave_final = s_vol_ave_final - offset
    s_vol_ave_transient = s_vol_ave_transient - offset

    # corrected surface average
    global_s_surf_ave_ss_corr = global_s_surf_ave_ss - s_vol_ave_final
    global_s_surf_ave_transient_corr = global_s_surf_ave_transient - s_vol_ave_transient

    check_steady_state(closure_data["times for transient data"], global_s_surf_ave_transient_corr)


    print("\nThe global steady state surface average BEFORE correction is ", global_s_surf_ave_ss, "\n")
    print("\nThe global volume average at the final time is ", s_vol_ave_final, "\n")
    print("\nThe global steady state surface average AFTER correction is ", global_s_surf_ave_ss_corr, "\n")
    
    # write results to closure data
    closure_data["global s surface average steady"] = global_s_surf_ave_ss_corr
    closure_data["global s surface average transient"] = global_s_surf_ave_transient_corr
    closure_data["global s volume average final"] = s_vol_ave_final
    closure_data["global s volume average transient"] = s_vol_ave_transient

    if write:
        with open(closure_data_dict_path, 'wb') as closure_data_file:
            pickle.dump(closure_data, closure_data_file)
        print("the closure results were written to the closure data dictionary")


def check_steady_state(t, s, window=0.5, rtol=1e-3):
    """
    Warns if the corrected global surface average has not reached steady state.

    Takes the range (maximum minus minimum) of the surface average over the last part of the
    simulation, relative to the largest magnitude reached during the run, so the check works in
    both dimensional and dimensionless units. Using the range over a long window means that a run
    stopped at the peak of the overshoot that the surface average shows early on is not mistaken
    for a steady one.

    Args:
        t (array): The times of the transient data.
        s (array): The corrected global surface average at each time.
        window (float): The fraction of the run, at its end, over which the range is measured. Default 0.5.
        rtol (float): The largest acceptable relative range. Default 1e-3.

    Returns:
        relative_range (float): The range over the window, relative to the largest magnitude.
    """

    t = np.asarray(t, dtype=float)
    s = np.asarray(s, dtype=float)
    scale = np.max(np.abs(s))
    if len(t) < 2 or scale == 0:
        return 0.0

    t_start = t[-1] * (1 - window)
    in_window = np.concatenate([[np.interp(t_start, t, s)], s[t > t_start]])
    relative_range = (np.max(in_window) - np.min(in_window)) / scale

    if relative_range > rtol:
        warnings.warn(
            f"The closure problem has not reached steady state: the global surface average varied by "
            f"{relative_range:.2%} over the last {window:.0%} of the simulation (limit {rtol:.2%}). "
            f"Run solve_closure again with a larger end_time or max_end_time, for example twice the current value of {t[-1]:g}.",
            UserWarning, stacklevel=2)

    return relative_range
