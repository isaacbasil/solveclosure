def write_thermophysicalProperties_file(file_path, particle_name, D):
    """
    Writes the thermophysicalProperties file for a multiparticle case.  
    
    Args:
        file_path (str): The absolute path to the thermophysicalProperties file. 
        particle_name (str): The name of the particle in format particle_i.
        D (float): The diffusivity of the AM in m2.s-1.

    Returns:
    """

    content = f"""
FoamFile
{{
    version     2.0;
    format      ascii;
    class       dictionary;
    location    "constant/{particle_name}";
    object      thermophysicalProperties;
}}

thermoType
{{
    type            heSolidThermo;
    mixture         pureMixture;
    transport       constIso;
    thermo          hConst;
    equationOfState rhoConst;
    specie          specie;
    energy          sensibleEnthalpy;
}}

mixture
{{
    specie
    {{
        molWeight       27;
    }}
    equationOfState
    {{
        rho             1;
    }}
    transport
    {{
        kappa           {D};
    }}
    thermodynamics
    {{
        Hf              0;
        Cp              1;
    }}
}}
"""
    
    with open(file_path, 'w') as f:
        f.write(content)

