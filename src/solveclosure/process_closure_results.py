import numpy as np 
import pickle
import subprocess
from solveclosure.utility import load_openfoam_data


def process_closure_results(case_dir, cbd_surf_por, sep_surf_por, write=True, multiparticle=True):
    """
    Processes the closure results from a solved OpenFOAM case, and writes them to the closure_data dictionary. 
    
    Args:
        case_dir (str): The path to the directory where the OpenFOAM case was solved.
        cbd_surf_por (float): The CBD surface porosity.
        sep_surf_por (float): The separator surface porosity.
        write (bool): To set to False to vot write results to the closure_dict, but only print them.
        multiparticle (bool): To set to True for a multiparticle case.

    Returns: 
        closure_data (dict): The dictionary containing the closure results and other image data.
    """

    def check_steady_state(t, s_surf, label):
        # checks that OpenFOAM solver reached steady state
        s1 = s_surf[-50]
        t1 = t[-50]
        s2 = s_surf[-1]
        t2 = s_surf[-1]

        if abs(s1 - s2) > 1:
            print(f"\n It appears that the closure problem for Particle {label} has not reached steady state: \
                    The value at time {t1} s is {s1}, whilst at {t2} s it is {s2}")

    if any([string in case_dir for string in ["multiparticle", "multi_particle", "with_interparticle_flux"]]) and not multiparticle:
        response = input("\n Multiparticle is set to False, but this looks like a multiparticle case. Are you sure you want to conitune? (y/n)").strip().lower()
        if response != "y":
            print("Aborting.")
            exit()
                
    closure_data_dict_path = case_dir + "closure_data.pickle"

    # make a backup 
    subprocess.run(["bash", "-c", f"cd {case_dir} && cp closure_data.pickle closure_data_backup.pickle"], check=False)

    with open(closure_data_dict_path, 'rb') as closure_data_file:
        closure_data = pickle.load(closure_data_file)

    if multiparticle:
        offset = closure_data["T offset"]
        closure_data["method"] = "multiparticle" 

    t_initiated = False

    no_file_found = {"elec" : 0, "cbd" : 0, "sep" : 0}

    surf_por = {"elec" : 1, "cbd" : cbd_surf_por, "sep" : sep_surf_por}

    for key in closure_data["particle data"].keys():
        
        particle_initiated = False

        for type in ["elec", "cbd", "sep"]:

            if multiparticle:
                s_surf_int_path = case_dir + f"/openfoam_case/postProcessing/particle_{key}/particle_{key}_surfaceIntegral_{type}/0/surfaceFieldValue.dat"
            else:              
                s_surf_int_path = case_dir + "particle_" + str(key) + f"/openfoam_case/postProcessing/surfaceIntegral_{type}/0/surfaceFieldValue.dat"

            
            try:
                t, s_surf_int_i = load_openfoam_data(s_surf_int_path)
            except FileNotFoundError:
                no_file_found[type] += 1
                continue
            
            if len(s_surf_int_i) == 0:
                print(f"\n Although a surface integral file existed for particle {key} with type {type} it is empty \n")
                continue 
            
            check_steady_state(t, s_surf_int_i, key)

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
        if multiparticle:
            s_vol_int_path = case_dir + f"/openfoam_case/postProcessing/particle_{key}/particle_{key}_volumeIntegral/0/volFieldValue.dat"
        else:              
            s_vol_int_path = case_dir + f"particle_{key}/openfoam_case/postProcessing/volumeIntegral/0/volFieldValue.dat" 

        try:
            t_vol, s_vol_int_i = load_openfoam_data(s_vol_int_path)
        except FileNotFoundError:
            print(f"\n No file found for the volume integral/average for particle {key}")
            continue  

        for t_idx in range(len(closure_data["times for transient data"])):
            global_sum_s_vol_int_transient[t_idx] += s_vol_int_i[t_idx]
 

    for type in ["elec", "cbd", "sep"]:
        print(f"\n No files found for type {type} for {no_file_found[type]} particles \n")

    
    # divde by A
    total_A = closure_data["total area (surface porosity included)"]

    global_s_surf_ave_transient = global_sum_s_surf_int_transient / total_A

    s_vol_ave_transient = global_sum_s_vol_int_transient / closure_data["total particle volume"]

    global_s_surf_ave_ss = global_s_surf_ave_transient[-1]

    s_vol_ave_final = s_vol_ave_transient[-1]

    # subtract offset for multiparticle method 
    if multiparticle:
        global_s_surf_ave_ss = global_s_surf_ave_ss - offset
        global_s_surf_ave_transient = global_s_surf_ave_transient - offset
        s_vol_ave_final = s_vol_ave_final - offset
        s_vol_ave_transient = s_vol_ave_transient - offset

    # corrected surface average
    global_s_surf_ave_ss_corr = global_s_surf_ave_ss - s_vol_ave_final
    global_s_surf_ave_transient_corr = global_s_surf_ave_transient - s_vol_ave_transient


    print("\n The global steady state surface average BEFORE correction is ", global_s_surf_ave_ss, "\n")
    print("\n The global volume average at the final time is ", s_vol_ave_final, "\n")
    print("\n The global steady state surface average AFTER correction is ", global_s_surf_ave_ss_corr, "\n")
    
    # write results to closure data
    closure_data["global s surface average steady"] = global_s_surf_ave_ss_corr
    closure_data["global s surface average transient"] = global_s_surf_ave_transient_corr
    closure_data["global s volume average final"] = s_vol_ave_final
    closure_data["global s volume average transient"] = s_vol_ave_transient

    if write:
        with open(closure_data_dict_path, 'wb') as closure_data_file:
            pickle.dump(closure_data, closure_data_file)
        print("the closure results were written to the closure data dictionary") 




            



  


