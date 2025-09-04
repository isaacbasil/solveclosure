def write_myFunctionsDict_multiparticle(file_path, neighbour_ids):
    """
    Writes the dictionary of functions to be included in system/controlDict. 
    For multiparticle option, this includes all particles as well as elec, cbd, and sep 
    
    Args:
        file_path (str): The absolute path to the myFunctionsDict file for the OpenFOAM case.  
        neighbour_ids (list): The IDs of particles which share a boundary with particle i.

    Returns:
    """

    str_list = ""
    for particle_id, neighbour_ids_i in neighbour_ids.items():
        name = f"particle_{particle_id}"
        str_list += f"#includeFunc {name}_volumeIntegral \n"
        for type in ["elec", "cbd", "sep"]:
            if type in neighbour_ids_i:
                str_list += f"#includeFunc {name}_surfaceIntegral_{type} \n"
    
    content = f"""

functions
{{
{str_list}
}}

"""
    
    with open(file_path, 'w') as f:
        f.write(content)
