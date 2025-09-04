def write_regionProperties_file(file_path, particle_names):
    """
    Writes the OpenFOAM regionProperties file for a multiparticle case.  
    
    Args:
        file_path (str): The absolute path to the regionProperties file for the OpenFOAM case. 
        particle_names (list): A list of all particle IDs

    Returns:
    """

    region_str = "(" + " ".join(particle_names) + ")"

    content = f"""
FoamFile
{{
    version     2.0;
    format      ascii;
    class       dictionary;
    location    "constant";
    object      regionProperties;
}}

regions
(
    fluid       ()
    solid       {region_str}
);
    """

    with open(file_path, 'w') as f:
        f.write(content)


