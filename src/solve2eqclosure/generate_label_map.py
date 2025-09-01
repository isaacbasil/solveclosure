# This file runs a waterhsed and generates a tif containing the particle id map

import numpy as np
import tifffile as tif
from scipy import ndimage as ndi
from skimage import measure, morphology, segmentation, filters
from matplotlib import pyplot as plt

def generate_label_map(input_path, write_path, show_image=False):
    """
    Generates and writes a label map for an electrode image using a watershed algorithm. 

    Args:
        input_path (str): The path to the electrode image (electrolyte labelled 0, active material 1, and CBD 2).
        write_path (str): The path to where the label map will be written to.
        
    Returns: 
    """

    def check_all_particles(img, label_map):
        n_particles = max(np.unique(label_map))

        for i in range(1, n_particles + 1):
            particle = np.copy(img[label_map == i])
            # check no electrolyte
            if not np.all(particle == 1):
                raise ValueError(f"Particle {i} contains electrolyte")
            # check am present
            if not np.any(particle == 1):
                raise ValueError(f"Particle {i} contains no AM")


    img = tif.imread(input_path)

    am_mask = (img == 1)

    # Compute distance transform
    distance = ndi.distance_transform_edt(am_mask)

    # Identify local maxima
    local_maxi = morphology.local_maxima(distance)

    # Label markers
    markers = measure.label(local_maxi)

    # Apply watershed
    label_map = segmentation.watershed(-distance, markers, mask=am_mask)


    if show_image:
        if img.shape[2] > 1e5:
            x = np.linspace(0, img.shape[0], 5)

            for val in x:
                if val > img.shape[0] - 1:
                    break
                plt.imshow(label_map[round(val), :, :])
                plt.show()
        else: 
            plt.imshow(label_map[:, :, 1])
            plt.show()


    check_all_particles(img, label_map)

    # Save result
    tif.imwrite(write_path, label_map.astype(np.uint16))