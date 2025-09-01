# makes the blockMeshDict file for OpenFOAM based on the image dimensions.

def make_blockMeshDict(file_path, img, voxel):
    """
    Writes the blockMeshDict file with the correct dimensions
    
    Args:
        file_path (str): The absolute path to the blockMeshDict file for the OpenFOAM case. 
        img (nd array): The electrode image.
        voxel (float): The voxel size in meters.

    Returns:
    """

    nx, ny, nz = img.shape

    content = f"""
FoamFile
{{
    version     2.0;
    format      ascii;
    class       dictionary;
    object      blockMeshDict;
}}

scale   {voxel};

vertices
(
    (0 0 0)    // vertex 0
    ({nx} 0 0)    // vertex 1
    ({nx} {ny} 0)    // vertex 2
    (0 {ny} 0)    // vertex 3
    (0 0 {nz})    // vertex 4
    ({nx} 0 {nz})    // vertex 5
    ({nx} {ny} {nz})    // vertex 6
    (0 {ny} {nz})    // vertex 7
);

blocks
(
    hex (0 1 2 3 4 5 6 7) ({nx} {ny} {nz}) simpleGrading (1 1 1)
);

edges
(
);

boundary
(
    outerWalls
    {{
        type patch;
        faces
        (
            (0 4 7 3)
            (2 6 5 1)
            (3 7 6 2)
            (1 5 4 0)
        );
    }}
);

"""
    
    with open(file_path, 'w') as output_file:
        output_file.write(content)
