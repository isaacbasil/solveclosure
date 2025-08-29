def write_surface_integral_func(file_path, particle_name, type):
    """
    type = "elec", "cbd", "sep"
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
