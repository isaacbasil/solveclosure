def write_p_file(file_path, particle_name):

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

