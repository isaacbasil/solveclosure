def write_fvOptions_file_multiparticle(file_path, particle_name, vol_source):
    """
    Writes the OpenFOAM BC file for a multiparticle case  
    
    Args:
        file_path (str): The absolute path to the fvOptions file for the OpenFOAM case. 
        particle_name (str): The name of the particle in format particle_i.
        vol_source (float): The source term within the AM volume.  

    Returns:
    """

    content = f"""
FoamFile
{{
    version     2.0;
    format      ascii;
    class       dictionary;
    location    "constant/{particle_name}";
    object      fvOptions;
}}

options
{{
    energySource
    {{
        type            scalarSemiImplicitSource;
        selectionMode   all;
        volumeMode      specific;

        injectionRateSuSp
        {{
            h          ({vol_source} 0); // W/m^3 == kg/m/s^3
        }}
    }}
}}
"""
    
    with open(file_path, 'w') as f:
        f.write(content)
