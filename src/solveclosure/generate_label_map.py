# This file runs a waterhsed and generates a tif containing the particle id map

import numpy as np
import tifffile as tif
from scipy import ndimage as ndi
from skimage import measure, morphology, segmentation, filters
from matplotlib import pyplot as plt

def generate_label_map(input_path, write_path, show_image=False, sigma=2.0, compactness=0.01):
    """
    Generates and writes a label map for an electrode image using a watershed algorithm. 

    Args:
        input_path (str): The path to the electrode image (electrolyte labelled 0, active material 1, and CBD 2).
        write_path (str): The path to where the label map will be written to.
        show_image (bool): Shows slice of the label map (useful for debugging).
        sigma (float): The standard deviation for Gaussian smoothing applied to the distance map. Prevents over-segmentation (higher sigma = fewer particles).
        compactness (float): A parameter for the watershed algorithm which adjusts region shapes. 
        
    Returns: 
    """

    def check_all_particles(img, label_map):
        n_particles = max(np.unique(label_map))

        if ((label_map == 0.0) & (img == 1.0)).any():
            raise ValueError("Some AM regions are were not labelled.")

        for i in range(1, n_particles + 1):
            particle = np.copy(img[label_map == i])
            # check no electrolyte
            if not np.all(particle == 1):
                raise ValueError(f"Particle {i} contains electrolyte")
            # check am present
            if not np.any(particle == 1):
                raise ValueError(f"Particle {i} contains no AM")
            
    def gap_filling(am_mask, label_map):
        # Sometimes not all AM regions are labeled. This merges unlabelled regions with their nearest neighbour. 

        unlabelled_mask = (label_map == 0) & am_mask

        filled_label_map = label_map.copy()

        # Compute distance transform *to nearest labelled pixel* and get indices of nearest labelled pixel
        dist, nearest_label_indices = ndi.distance_transform_edt(
            (filled_label_map > 0),
            return_indices=True
        )

        # Map unlabeled pixels to the nearest labelled pixel’s label
        nearest_labels = filled_label_map[tuple(nearest_label_indices)]
        filled_label_map[unlabelled_mask] = nearest_labels[unlabelled_mask]

        return filled_label_map


    img = tif.imread(input_path)

    am_mask = (img == 1)

    # Compute distance transform
    distance = ndi.distance_transform_edt(am_mask)

    # Smooth distance map to prevent over-segmentation 
    distance = ndi.gaussian_filter(distance, sigma=sigma)  

    # Identify local maxima
    local_maxi = morphology.local_maxima(distance)

    # Label markers
    markers = measure.label(local_maxi)

    # Apply watershed
    label_map = segmentation.watershed(-distance, markers, mask=am_mask, compactness=compactness)

    if ((label_map == 0.0) & (img == 1.0)).any():
        label_map = gap_filling(am_mask, label_map)

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