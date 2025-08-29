import numpy as np

def calculate_area_and_volume(img, voxel, cbd_surface_porosity):
    # calculates surface area and active material volume

    nx, ny, nz = img.shape
    count_am_cbd = 0
    count_am_elec = 0
    #count_am_sep = 0 # TODO: add in accounting for sep! 

    # calculate surface areas, this is copied from function in compare_dfn_dns_workflow 
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
