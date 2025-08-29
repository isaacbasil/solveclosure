def write_thermophysicalProperties_file(file_path, particle_name, D):

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

