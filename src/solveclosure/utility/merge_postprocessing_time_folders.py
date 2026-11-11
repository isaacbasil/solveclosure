import os
import shutil


def merge_postprocessing_time_folders(of_case_dir):
    """
    Merges the function object output of a continued OpenFOAM run into one file per function object.

    When the solver is relaunched from a later time, OpenFOAM writes the function object output
    (for example surfaceFieldValue.dat) into a new folder named after the start time, next to the
    original "0" folder. This function joins the files of all time folders, in time order, into the
    file in the earliest folder and removes the other folders, so the output looks like that of one
    continuous simulation. If a run started before the end of an earlier one, its values replace
    the earlier values after its start time.

    Args:
        of_case_dir (str): The path to the OpenFOAM case (the folder containing postProcessing).

    Returns:
        n_merged (int): The number of function object folders that were merged.
    """

    post_dir = os.path.join(of_case_dir, "postProcessing")
    if not os.path.isdir(post_dir):
        return 0

    n_merged = 0
    for root, dirs, _ in os.walk(post_dir):
        time_folders = []
        for d in dirs:
            try:
                time_folders.append((float(d), d))
            except ValueError:
                continue
        if len(time_folders) < 2:
            continue

        time_folders.sort()
        first = os.path.join(root, time_folders[0][1])
        file_names = sorted(f for f in os.listdir(first) if os.path.isfile(os.path.join(first, f)))

        for file_name in file_names:
            header = []
            data = []  # (time, line)
            for start, folder in time_folders:
                path = os.path.join(root, folder, file_name)
                if not os.path.isfile(path):
                    continue
                with open(path) as f:
                    lines = f.readlines()
                if folder == time_folders[0][1]:
                    header = [line for line in lines if line.startswith("#")]
                # values after this start time come from this run (it does not write the start time itself)
                data = [(t, line) for t, line in data if t <= start * (1 + 1e-12)]
                data += [(float(line.split()[0]), line) for line in lines if line.strip() and not line.startswith("#")]

            with open(os.path.join(first, file_name), "w") as f:
                f.writelines(header)
                f.writelines(line if line.endswith("\n") else line + "\n" for _, line in data)

        for _, folder in time_folders[1:]:
            shutil.rmtree(os.path.join(root, folder))
        n_merged += 1

        dirs[:] = [d for d in dirs if d == time_folders[0][1] or d not in {name for _, name in time_folders}]

    return n_merged
