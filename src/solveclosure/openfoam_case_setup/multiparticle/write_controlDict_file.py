def write_controlDict_file(file_path, dimensionless, time_params):
    """
    Writes the OpenFOAM controlDict file for a multiparticle case. Final time and t step will be different depending on whether dimensionless is True or False.  
    
    Args:
        file_path (str): The absolute path to the p file for the OpenFOAM case. 
        dimensionless (bool): Whether the case is dimensionless or not.
        time_params (dict): A dictionary specifying time parameters. If None, default values will be used.

    Returns:
    """
    
    if time_params is None:
        if dimensionless:
            time_params = {"T_end": 0.0056, "dt": 1e-8, "write_interval": 0.0014}
        else:
            time_params = {"T_end": 800.0, "dt": 1e-3, "write_interval": 200}

    content = f"""
FoamFile
{{
    version     2.0;
    format      ascii;
    class       dictionary;
    location    "system";
    object      controlDict;
}}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

application     chtMultiRegionFoam;

startFrom       startTime;

startTime       0;

stopAt          endTime;

endTime         {time_params["T_end"]};

deltaT          {time_params["dt"]};

writeControl    adjustableRunTime;

writeInterval   {time_params["write_interval"]};

purgeWrite      0;

writeFormat     binary;

writePrecision  10;

writeCompression off;

timeFormat      general;

timePrecision   6;

runTimeModifiable true;

maxCo           1.0;

maxDi           10.0;

adjustTimeStep  yes;

#include myFunctionsDict
"""
    
    with open(file_path, 'w') as f:
        f.write(content)