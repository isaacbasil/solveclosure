def write_p_file(file_path, particle_name):
    """
    Writes the OpenFOAM p file for a multiparticle case. This file does nothing, but is necessary for the OpenFOAM solver.  
    
    Args:
        file_path (str): The absolute path to the p file for the OpenFOAM case. 
        particle_name (str): The name of the particle in format particle_i.

    Returns:
    """

    content = f"""
FoamFile
{{
    version     2.0;
    format      ascii;
    class       volScalarField;
    location    "0/{particle_name}";
    object      p;
}}

dimensions      [1 -1 -2 0 0 0 0];

internalField   uniform 0;

boundaryField
{{
    #includeEtc "caseDicts/setConstraintTypes"

    ".*"
    {{
        type            calculated;
        value           $internalField;
    }}
}}
"""
    
    with open(file_path, 'w') as f:
        f.write(content)

