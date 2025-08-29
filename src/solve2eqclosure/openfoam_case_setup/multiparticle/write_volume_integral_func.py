def write_volume_integral_func(file_path, particle_name, multiparticle=True):
        
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
