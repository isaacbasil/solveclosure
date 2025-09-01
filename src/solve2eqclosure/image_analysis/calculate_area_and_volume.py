import numpy as np

def calculate_area_and_volume(img, voxel, cbd_surface_porosity):
    # calculates surface area and active material volume
    """
    Calculates the source terms for the DIMENSIONAL closure problem PDE.
    
    Args:
        img (nd array): The electrode image.
        voxel (float): The voxel size in meters.
        cbd_surface_porosity (float): The CBD surface porosity.

    Returns: 
        area_am_elec (float): The total area of the AM-elec boundary (m2).
        area_am_cbd (float): The total area of the AM-CBD boundary (m2).
        total_area (float): The total surface area (with surface porosity of CBD accounted for).
        V_am (float): The total volume of the AM. 
    """

    nx, ny, nz = img.shape
    count_am_cbd = 0
    count_am_elec = 0

    # calculate surface areas 
    for i in range(nx):
        for j in range(ny):
            for k in range(nz):

                # Check front neighbor
                if i + 1 < nx:
                    if (img[i, j, k] == 1 and img[i + 1, j, k] == 0) or (img[i, j, k] == 0 and img[i + 1, j, k] == 1):
                        count_am_elec += 1
                    if (img[i, j, k] == 1 and img[i + 1, j, k] == 2) or (img[i, j, k] == 2 and img[i + 1, j, k] == 1):
                        count_am_cbd += 1

                # check right neighbour
                if j + 1 < ny:
                    if (img[i, j, k] == 1 and img[i, j + 1, k] == 0) or (img[i, j, k] == 0 and img[i, j + 1, k] == 1):
                        count_am_elec += 1
                    if (img[i, j, k] == 1 and img[i, j + 1, k] == 2) or (img[i, j, k] == 2 and img[i, j + 1, k] == 1):
                        count_am_cbd += 1

                # check upper neighbour
                if k + 1 < nz:
                    if (img[i, j, k] == 1 and img[i, j, k + 1] == 0) or (img[i, j, k] == 0 and img[i, j, k + 1] == 1):
                        count_am_elec += 1
                    if (img[i, j, k] == 1 and img[i, j, k + 1] == 2) or (img[i, j, k] == 2 and img[i, j, k + 1] == 1):
                        count_am_cbd += 1


    # assuming each interface is square, and that they are all the same size
    face_area = voxel ** 2
    area_am_elec = face_area * count_am_elec
    area_am_cbd = face_area * count_am_cbd
                
    total_area = area_am_elec + area_am_cbd * cbd_surface_porosity
    voxel_vol = voxel ** 3
    V_am = np.sum(img[img == 1]) * voxel_vol

    return area_am_elec, area_am_cbd, total_area, V_am
