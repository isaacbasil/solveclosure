def check_for_existing_solutions(case_dir):
    # checks if a closure solution already exists and prompts user 

    if any(os.path.isdir(os.path.join(case_dir, d)) and d.startswith("particle") for d in os.listdir(case_dir)):

        response = input("\n Closure problem solutions were found in this case_dir already. Are you sure you want to continue? (y/n)").strip().lower()

        if response != "y":
            print("Aborting.")
            exit()
