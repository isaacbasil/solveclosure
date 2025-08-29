import tifffile as tif
import numpy as np
import matplotlib.pyplot as plt
from skimage import measure
from scipy import ndimage
from scipy.ndimage import binary_dilation

def subdivide_image_using_label_map(particle_id_path, original_tif, show_subsections=False):
    """
    Subdivides a tif file using particle IDs and displays the subsections.
    
    Args:
        particle_id_path (str): Path to the tif file containing particle IDs.
        original_tif (nd array): The original tif file to be subdivided.
    """

    def remove_isolated_am_regions(img, particle_id, raise_error=True):
        # this function removes all except the largest AM region present in the subsection, since a particle should be one domain. 
        # Isolated regions can be caused by errors in the image segmentation
        mask = img == 1
        labelled_components, num_components = measure.label(mask, connectivity=1, return_num=True)

        labels, counts = np.unique(labelled_components, return_counts=True)
        labels = labels[1:] # electrolyte is always first index, remove this
        counts = counts[1:]
        if len(counts) > 0:
            most_frequent = labels[np.argmax(counts)]

            remove_ids = (labelled_components != most_frequent) & (labelled_components > 0) # ensures cbd not removed

            if np.sum(remove_ids) > 0:
                plt.imshow(img)
                plt.show()
                if raise_error:
                     raise ValueError(f"Isolated AM was found in Particle {particle_id} subsection.")
                else:
                    print(f"Isolated AM was found in Particle {particle_id} subsection. It will be cleaned \n")

            img[remove_ids] = 0

        if np.sum(img == 1) == 0:
            raise ValueError(f"No AM in subsection for Particle {particle_id}")

        return img
    

    def recognise_other_am_particles(subsection, subsection_labels, particle_id):
        # this function relabels other AM particles in the image subsection, so that AM-AM boundaries can be recognised later. 
        # it also returns the IDs of neighbouring particles
        # the label chosen for other particles is 3 
        
        # ids to relabel to 3
        relabel_ids = (subsection_labels != particle_id) & (subsection == 1)

        # gettings IDs of neighbouring particles
        neighbour_ids = []
        other_particle_ids = np.unique(subsection_labels[relabel_ids]) # ids of other particles in subsection

        primary_particle_mask = subsection_labels == particle_id
        for other_id in other_particle_ids:
            other_particle_mask = np.copy(subsection_labels) == other_id
            other_particle_mask_dilated = binary_dilation(other_particle_mask)
            # check if dilated mask overlaps with main particle
            if np.any(primary_particle_mask & other_particle_mask_dilated):
                neighbour_ids.append(other_id)

        # check if particle touches elec or cbd
        dilated_masks = {"elec": binary_dilation(np.copy(subsection) == 0),
                         "cbd": binary_dilation(np.copy(subsection) == 2),}
        for key, mask in dilated_masks.items():
            if np.any(primary_particle_mask & mask):
                neighbour_ids.append(key)

        # tag other particles as 3 
        subsection[relabel_ids] = 3

        return subsection, neighbour_ids
    
    def calculate_centre_coordinates(label_map):
        # takes the labelled image and returns particle centres (in voxel position)
        labels_present = np.unique(label_map)
        labels_present = labels_present[labels_present != 0]
        centres = ndimage.center_of_mass(label_map > 0, labels=label_map, index=labels_present)
        return centres

            

    label_map = tif.imread(particle_id_path)

    # convert from bool if needed
    if original_tif.dtype == bool:
        print("\n Warning: the original tif is in boolean format. This may cause problems in certain scripts \n")
        original_tif = original_tif.astype(int)

    n_particles = np.max(label_map)

    centres = calculate_centre_coordinates(label_map)


    min_coords = {}
    max_coords = {}
    subsections = {}
    neighbour_ids = {}
    for i in range(1, n_particles + 1):
        min_coords[i] = []
        max_coords[i] = []
        particle_member_coords = np.where(label_map == i)
        for idx in range(3):
            min_coord = np.min(particle_member_coords[idx])
            max_coord = np.max(particle_member_coords[idx])
            # pad the min and max coordinates by 1 to include the boundary
            min_coords[i].append(min_coord - 1 if min_coord > 0 else min_coord)
            max_coords[i].append(max_coord + 1 if max_coord < original_tif.shape[idx] - 1 else max_coord)


        subsection = np.copy(original_tif[min_coords[i][0]:max_coords[i][0]+1,
                                min_coords[i][1]:max_coords[i][1]+1,
                                min_coords[i][2]:max_coords[i][2]+1])
        
        subsection_labels = np.copy(label_map[min_coords[i][0]:max_coords[i][0]+1,
                                min_coords[i][1]:max_coords[i][1]+1,
                                min_coords[i][2]:max_coords[i][2]+1])
        
        # recognise any other particles in the subsection
        subsection, neighbour_ids[i] = recognise_other_am_particles(subsection, subsection_labels, i)

        # plt.imshow(subsection_labels)
        # plt.show()
        
        # clean any other isolated regions incase of segmentation fault
        subsection = remove_isolated_am_regions(subsection, i)
        
        subsections[i] = np.copy(subsection)

        if show_subsections:
            plt.imshow(subsections[i][:, :, 0])
            plt.title(f"Particle {i} Subsection")
            plt.show()

    return subsections, centres, neighbour_ids

    
