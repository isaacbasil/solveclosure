import os 
def check_for_existing_solutions(case_dir):
    """
    Checks if a closure solution already exists in the case directory provided and prompts user. 
    
    Args:
        case_dir (str): The path to the directory where the OpenFOAM case will be built.

    Returns: 
    """

    solutions_exist = os.path.isdir(os.path.join(case_dir, "openfoam_case"))

    if solutions_exist:
        response = input("\n Closure problem solutions were found in this case_dir already. Are you sure you want to continue? (y/n)").strip().lower()

        if response != "y":
            print("Aborting.")
            exit()
