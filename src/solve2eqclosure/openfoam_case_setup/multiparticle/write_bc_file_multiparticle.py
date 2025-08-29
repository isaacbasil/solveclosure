def write_bc_file_multiparticle(file_path, particle_name, elec_source, cbd_source, neighbour_ids, T_offset, allow_flux=True):
    # write the file for T for each region

    content = f"""
FoamFile
{{
    version     2.0;
    format      ascii;
    class       volScalarField;
    location    "0/{particle_name}";
    object      T;
}}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

dimensions      [ 0 0 0 1 0 0 0 ];

internalField   uniform {T_offset};

boundaryField
{{
    #includeEtc "caseDicts/setConstraintTypes"

    {particle_name}_to_Elec
    {{
        type            fixedGradient;
        gradient        uniform {elec_source};
    }}
    outerWalls
    {{
        type            zeroGradient;
    }}
    defaultFaces
    {{
        type            empty;
    }}
    oldInternalFaces
    {{
        type            empty;
    }}

"""
    if cbd_source:
        content += f"""
    {particle_name}_to_CBD
    {{
        type            fixedGradient;
        gradient        uniform {cbd_source};
    }}
"""

    # for older versions change to compressible::turbulentTemperatureCoupledBaffleMixed and delete qr entry
    
    for id in neighbour_ids:
        if isinstance(id, str):
            continue

        neighbour_name = f"particle_{id}"

        if allow_flux:
            content += f"""
    {particle_name}_to_{neighbour_name}
    {{
        type            compressible::turbulentTemperatureRadCoupledMixed;
        qr              none;
        value           $internalField;
        Tnbr            T;
        kappaMethod     solidThermo;
    }}
"""
        # if flux not allowed between particles...
        else:
            content += f"""
    {particle_name}_to_{neighbour_name}
    {{
        type            zeroGradient;
    }}
"""
        
    # add final bracket
    content += "}"

    with open(file_path, 'w') as f:
        f.write(content)
        print("\n the bc file written \n")

