def write_surface_integral_func(file_path, particle_name, type):
    """
    Writes the surface integral function for a multiparticle case.  
    
    Args:
        file_path (str): The absolute path to the surface integral function file. 
        particle_name (str): The name of the particle in format particle_i.
        type (str): The type of boundary. Can be "elec", "cbd", "sep". 

    Returns:
    """

    if type == "elec":
        extension = "_to_Elec"
    elif type == "cbd":
        extension = "_to_CBD"
    elif type == "sep": 
        extension = "_to_Sep" 
    else:
        raise ValueError("Type not recognised")
          
    patch_name = particle_name + extension

    content = f"""
type            surfaceFieldValue;
libs            ("libfieldFunctionObjects.so");
log             true;
writeFields     false;
regionType      patch;
region          {particle_name};
name            {patch_name};
operation       areaIntegrate;
weightField     none;
mode            magnitude;
fields          (T);
writeControl    timeStep;
writeInterval   1; 
"""
    
    with open(file_path, 'w') as f:
        f.write(content)
