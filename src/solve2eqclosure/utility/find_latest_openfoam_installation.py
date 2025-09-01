import os
import glob
import subprocess

def find_latest_openfoam_installation():
    """
    Searches typical locations to find the latest OpenFOAM installation
    
    Args:

    Returns: 
        the command necessary to load an openfoam terminal
    """

    def find_all_openfoam_installations():
        """Search common system paths for OpenFOAM installations."""
        candidates = []

        # Common install locations
        search_paths = [
            "/opt",          # e.g. /opt/openfoam10
            "/usr/lib/openfoam",      # e.g. /usr/lib/openfoam/openfoam2206
            "/usr/local",    # in case of custom installs
        ]

        for base in search_paths:
            candidates.extend(glob.glob(os.path.join(base, "openfoam*")))

        # Filter only directories
        candidates = [c for c in candidates if os.path.isdir(c)]
        return sorted(candidates)


    def pick_latest(installations):
        """Pick the latest OpenFOAM version (naive: sort by string)."""
        if not installations:
            return None
        return sorted(installations)[-1]


    def launch_openfoam_terminal(openfoam_path):
        """Launch a bash shell with OpenFOAM environment sourced."""
        # OpenFOAM installations usually have an etc/bashrc script
        bashrc_path = os.path.join(openfoam_path, "etc", "bashrc")

        if not os.path.isfile(bashrc_path):
            raise FileNotFoundError(f"No bashrc found at {bashrc_path}")

        print(f"Launching OpenFOAM from {openfoam_path} ...")

        # Start interactive shell with OpenFOAM sourced
        subprocess.run(["bash", "-i", "-c", f"source {bashrc_path}; exec bash"])


    installs = find_all_openfoam_installations()
    print(installs)
    if not installs:
        print("No OpenFOAM installations found in common paths.")
        exit(1)

    latest = pick_latest(installs)
    print("Available OpenFOAM installations:")
    for i, inst in enumerate(installs):
        print(f"  {i+1}: {inst}")
    print(f"\nSelected latest: {latest}")

    bashrc_path = os.path.join(latest, "etc", "bashrc")
    cmd = f"source {bashrc_path}"
    print(f"The command used to launch OpenFOAM terminals will be: {cmd}")

    return cmd

        
