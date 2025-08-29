def return_x_positions(centres, voxel):
    x_positions_voxel = [coord[0] for coord in centres]
    x_positions_m = [val * voxel for val in x_positions_voxel]
    return x_positions_m
