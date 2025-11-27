from solveclosure.image_analysis.calculate_area_and_volume import calculate_area_and_volume
import numpy as np

def calculate_source_terms_dimensionless(img, voxel, cbd_surface_porosity, L):
    """
    Calculates the source terms for the DIMENSIONLESS closure problem PDE.
    
    Args:
        img (nd array): The electrode image.
        voxel (float): The voxel size in meters.
        cbd_surface_porosity (float): The CBD surface porosity.
        L (float): The lengthscale used (m) to non-dimensionalise the problem.

    Returns: 
        dimensionless_S_vol (float): The volume source term.
        dimensionless_bc_elec (float): The AM-elec boundary source term.  
        dimensionless_bc_cbd (float): The AM-CBD boundary source term.  
        total_area (float): The total surface area (with surface porosity of CBD accounted for).
        V_am (float): The total volume of the AM. 
    """

    area_am_elec, area_am_cbd, total_area, V_am = calculate_area_and_volume(img, voxel, cbd_surface_porosity)
    
    F = 96485
    dimensionless_S_vol = L * total_area / V_am 

    dimensionless_bc_elec = - 1

    if area_am_cbd != 0:
        dimensionless_bc_cbd = - cbd_surface_porosity 
    else:
        dimensionless_bc_cbd = False

    if any([np.isnan(val) for val in [dimensionless_S_vol, dimensionless_bc_elec, dimensionless_bc_cbd]]):
        raise ValueError("One of the source terms is NaN!")
    
    return dimensionless_S_vol, dimensionless_bc_elec, dimensionless_bc_cbd, total_area, V_am
