import os 
def check_for_existing_solutions(case_dir, multiparticle=True):
    """
    Checks if a closure solution already exists in the case directory provided and prompts user. 
    
    Args:
        case_dir (str): The path to the directory where the OpenFOAM case will be built.
        multiparticle (bool): Set to True for a multiparticle case. 

    Returns: 
    """

    if multiparticle:
        solutions_exist = os.path.isdir(os.path.join(case_dir, "openfoam_case"))
    else:
        solutions_exist = any(os.path.isdir(os.path.join(case_dir, d)) and d.startswith("particle") for d in os.listdir(case_dir))

    if solutions_exist:
        response = input("\n Closure problem solutions were found in this case_dir already. Are you sure you want to continue? (y/n)").strip().lower()

        if response != "y":
            print("Aborting.")
            exit()
