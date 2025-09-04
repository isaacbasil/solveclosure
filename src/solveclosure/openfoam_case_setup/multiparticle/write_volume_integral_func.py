def write_volume_integral_func(file_path, particle_name):
    """
    Writes the volume integral function file for a multiparticle case.  
    
    Args:
        file_path (str): The absolute path to the volume integral function file. 
        particle_name (str): The name of the particle in format particle_i.

    Returns:
    """
        
    vol_name = particle_name

    content = f"""
type            volFieldValue;
libs            ("libfieldFunctionObjects.so");
log             true;
writeFields     false;
regionType      cellZone;
region          {vol_name};
name            {vol_name};
operation       volIntegrate;
weightField     none;
fields          (T);
writeControl    timeStep;
writeInterval   1; 
"""
    
    with open(file_path, 'w') as f:
        f.write(content)
