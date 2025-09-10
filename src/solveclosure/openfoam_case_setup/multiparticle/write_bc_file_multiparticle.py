def write_bc_file_multiparticle(file_path, particle_name, elec_source, cbd_source, neighbour_ids, T_offset, allow_flux=True):
    """
    Writes the OpenFOAM BC file for a multiparticle case  
    
    Args:
        file_path (str): The absolute path to the BC file (named T) for the OpenFOAM case. 
        particle_name (str): The name of the particle in format particle_i.
        elec_source (float): The source term at the AM-elec boundary.  
        cbd_source (float): The source term at the AM-CBD boundary.   
        neighbour_ids (list): The IDs of particles which share a boundary with particle i.
        T_offset (float): A large number to prevent the OpenFOAM solver from encountering negative 'temperatures'.  
        allow_flux(bool): True for Option 1, False for Option 2 (see documentation).

    Returns:
    """

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

