# this file builds the topoSetDict using the splitMeshRegions method, which is faster than the previous methods.

import tifffile as tif 
import numpy as np
import sys 
import os
import time 
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def make_topoSetDict(topoSetDict_path, img, multi_particle=False, label_map=None):
    """
    Writes the topoSetDict file for use with the splitMeshRegions method in Openfoam.
    
    Args:
        file_path (str): The absolute path to the topoSetDict file for the OpenFOAM case. 
        img (nd array): The electrode image.
        multiparticle (bool): Set to True if a multiparticle case is being solved. 
        label_map (nd array): A map identifying particle IDs (beginning at 1). Must be provided if multiparticle is True. 

    Returns:
    """

    def initialise_topo_file():
        
        content = """
FoamFile
{
    version     2.0;
    format      ascii;
    class       dictionary;
    object      topoSetDict;
}

"""
        # initialise actions 
        content += "\n" + "actions" + "\n("

        return content
    
    

    def add_region(input_content, region_name, box_tag):
        
        region_block = f"""
    {{
            name    {region_name};
            type    cellZoneSet;
            action  new;
            source  setToCellZone;
            sourceInfo
            {{
                set {box_tag}; 
            }}
    }}"""
        return input_content + "\n" + region_block


    def add_topo_labelToCell(input_content, id_list, name):

        id_list = "\n".join(str(n) for n in id_list)

        block = f"""{{
            name    {name};
            type    cellSet;
            action  new;
            source  labelToCell;
            value
            (
                {id_list}
            );
    }}"""
        
        return input_content + "\n" + block


    start_time = time.time()    

    F = 96485

    topo_content = initialise_topo_file()
    

    nx, ny, nz = img.shape

    if multi_particle:
        n_particles = np.max(np.unique(label_map))
        particle_cell_lists = {}
        for i in range(1, n_particles + 1):
            particle_cell_lists[i] = []
    else:
        am_id_list = []
        other_am_id_list = [] # ids for other AM particles in the subsection

    elec_id_list = [] 
    cbd_id_list = [] 


    cell_action = "new" 
    for i in range(0, nx):
        for j in range(0, ny):
            for k in range(0, nz):
                phase_id = int(img[i, j, k])
                cell_id = i + nx * j + nx * ny * k
                if phase_id == 1:
                    if multi_particle:
                        particle_cell_lists[label_map[i, j, k]].append(cell_id)
                    else:
                        am_id_list.append(cell_id)
                elif phase_id == 0:
                    elec_id_list.append(cell_id)
                elif phase_id == 2:
                    cbd_id_list.append(cell_id)
                elif phase_id == 3:
                    if not multi_particle:
                        other_am_id_list.append(cell_id)
                else:
                    raise ValueError("Unknown phase id in image: " + str(phase_id))
    
    
    if multi_particle:
        for key, cell_list in particle_cell_lists.items():
            region_label = f"c_am_{key}"
            topo_content = add_topo_labelToCell(topo_content, cell_list, region_label)
    else:
        topo_content = add_topo_labelToCell(topo_content, am_id_list, "c_am")
        if other_am_id_list:
            topo_content = add_topo_labelToCell(topo_content, other_am_id_list, "c_other_am")

    if elec_id_list:
        topo_content = add_topo_labelToCell(topo_content, elec_id_list, "c_elec")
    if cbd_id_list:
        topo_content = add_topo_labelToCell(topo_content, cbd_id_list, "c_cbd")

    
    
    # now define regions
    if multi_particle:
        for key, cell_list in particle_cell_lists.items():
            region_label = f"c_am_{key}"
            region_name = f"particle_{key}"
            topo_content = add_region(topo_content, region_name, region_label)
    else:
        topo_content = add_region(topo_content, "AM", "c_am")
        if other_am_id_list:
            topo_content = add_region(topo_content, "otherAM", "c_other_am")

    if elec_id_list:
        topo_content = add_region(topo_content, "Elec", "c_elec")
    if cbd_id_list:
        topo_content = add_region(topo_content, "CBD", "c_cbd")
        
    
    # close actions and add openFOAM footer
    topo_content += "\n);\n" + "// ************************************************************************* //\n"
    with open(topoSetDict_path, 'w') as output_file:
        output_file.write(topo_content)


    end_time = time.time()
    print("The time taken to write the topoSet file is ", str(end_time - start_time), " s")

