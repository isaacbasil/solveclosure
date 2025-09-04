def return_x_positions(centres, voxel):
    """
    Calculate the x positions of particle centres.
    
    Args:
        centres (list): A list of all centre coordinates.
        voxel (float): The voxel size in meters.
    """
    x_positions_voxel = [coord[0] for coord in centres]
    x_positions_m = [val * voxel for val in x_positions_voxel]
    return x_positions_m
