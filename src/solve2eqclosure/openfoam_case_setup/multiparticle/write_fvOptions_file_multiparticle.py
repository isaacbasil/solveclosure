def write_fvOptions_file_multiparticle(file_path, particle_name, vol_source):
    # writes the fvOptions file for each region, which contains the source term

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
