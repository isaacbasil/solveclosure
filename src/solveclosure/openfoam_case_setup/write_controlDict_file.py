def write_controlDict_file(file_path, dimensionless, end_time, write_interval, start_from="startTime"):
    """
    Writes the OpenFOAM controlDict file.
    
    Args:
        file_path (str): The absolute path to the controlDict file for the OpenFOAM case.
        dimensionless (bool): Whether the case is dimensionless or not. Sets the initial time step.
        end_time (float): The simulation end time (dimensionless, or in seconds for a dimensional case).
        write_interval (float): The interval at which the 3D fields are written.
        start_from (str): "startTime" to start from time 0, or "latestTime" to continue from the latest saved time. Default "startTime".

    Returns:
    """

    # initial time step; the solver then adjusts it (adjustTimeStep, maxDi)
    dt = 1e-8 if dimensionless else 1e-3
    dt = min(dt, end_time / 1000)

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

startFrom       {start_from};

startTime       0;

stopAt          endTime;

endTime         {end_time};

deltaT          {dt};

writeControl    adjustableRunTime;

writeInterval   {write_interval};

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