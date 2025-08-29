from solve2eqclosure.image_analysis.calculate_area_and_volume import calculate_area_and_volume

def check_and_write_area_and_volume_total(closure_data, entire_img, voxel, cbd_surface_porosity):
    # checks that the sum of area and volume from the particles matches the total image

    if entire_img.dtype == bool:
        entire_img = entire_img.astype(int)

    area_am_elec, area_am_cbd, total_area, V_am = calculate_area_and_volume(entire_img, voxel, cbd_surface_porosity)

    pp_total_area = 0 # per particle area sum 
    pp_V_am = 0 

    for key, value in closure_data["particle data"].items():
        pp_total_area += value["particle surface area"]
        pp_V_am += value["particle volume"]

    if abs(pp_total_area - total_area) / total_area * 100 > 1:
        raise ValueError("The total area from the image does not agree with the total area summed from individiual particles")
    
    if abs(pp_V_am - V_am) / V_am * 100 > 1:
        raise ValueError("The total AM volume from the image does not agree with the total volume summed from individiual particles")
    
    closure_data["total area (surface porosity included)"] = total_area
    closure_data["am-elec area"] = area_am_elec
    closure_data["am-cbd area (surface porosity omitted)"] = area_am_cbd
    closure_data["total particle volume"] = V_am
    
    return closure_data
