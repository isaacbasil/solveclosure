from solve2eqclosure.image_analysis.calculate_area_and_volume import calculate_area_and_volume
import numpy as np

def calculate_source_terms(img, voxel, cbd_surface_porosity, D_s):
    # calculates the source terms for the DIMENSIONAL closure problem

    area_am_elec, area_am_cbd, total_area, V_am = calculate_area_and_volume(img, voxel, cbd_surface_porosity)
    
    F = 96485
    dimensional_S_vol = 1 / F * total_area / V_am 

    dimensional_bc_elec = - 1 / (D_s *F)


    print("\n The dimensional source term added to fvOptions is ", dimensional_S_vol)
    print("\n The dimensional gradient BC is ", dimensional_bc_elec)

    if area_am_cbd != 0:
        dimensional_bc_cbd = cbd_surface_porosity * - 1 / (D_s *F)
        print("\n The dimensional gradient BC at the CBD interface is ", dimensional_bc_cbd)
    else:
        dimensional_bc_cbd = False

    if any([np.isnan(val) for val in [dimensional_S_vol, dimensional_bc_elec, dimensional_bc_cbd]]):
        raise ValueError("One of the source terms is NaN!")
    
    return dimensional_S_vol, dimensional_bc_elec, dimensional_bc_cbd, total_area, V_am
