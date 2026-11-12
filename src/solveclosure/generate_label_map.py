# Generates a label map (one ID per active material particle) for an electrode image with a watershed.

import os
import warnings

import numpy as np
import tifffile as tif
from scipy import ndimage as ndi
from skimage import measure, morphology, segmentation

MAXIMA_ALGORITHMS = ("h_maxima", "local_maxima", "peak_local_max")


def generate_label_map(input_path, write_path, *, maxima_algorithm="h_maxima", h=0.75, sigma=None, compactness=None,
                       min_distance=5, save_image=True, save_stats=True):
    """
    Generates and writes a label map for an electrode image using a marker-based watershed.

    Each active material (AM) particle gets its own ID, starting at 1; all other voxels are 0. The
    particles are separated by a watershed on the distance map of the AM (the distance of each AM
    voxel to the nearest non-AM voxel), starting from markers placed at the peaks of the distance map.
    Works for 2D and 3D images.

    Particles that touch along a large, flat contact (with no narrowing between them) cannot be
    separated from their shape alone; check the result, for example with ``save_image``.

    Args:
        input_path (str): The path to the electrode image (electrolyte 0, AM 1, CBD 2, separator 3).
        write_path (str): The path the label map tif is written to. Saved as uint16, or as uint32 if
            there are more than 65535 particles.
        maxima_algorithm (str): How the markers are found. "h_maxima" (default) keeps the peaks of the
            distance map that stand at least ``h`` voxels above the lowest point between them and a
            higher peak, which ignores flat tops and small bumps. "local_maxima" uses every local
            maximum of the smoothed distance map (the method of solveclosure 0.1.0). "peak_local_max"
            uses skimage's peak_local_max with ``min_distance``.
        h (float): The minimum height, in voxels, of a peak for "h_maxima". Lower values split more
            particles, higher values merge more. Default 0.75.
        sigma (float, optional): Standard deviation, in voxels, of the Gaussian smoothing of the distance
            map. Default 0.75 for "h_maxima" and 2.0 for the other algorithms.
        compactness (float, optional): Watershed compactness. Default 0 for "h_maxima" and 0.01 for the
            other algorithms.
        min_distance (int): The minimum distance between peaks, only used by "peak_local_max".
        save_image (bool): Save a png of the label map next to ``write_path`` (``<name>_slices.png``):
            four slices evenly spaced along x (axis 0) for a 3D image, or the whole label map for a 2D
            image. Default True.
        save_stats (bool): Save a png of the particle count and size distribution next to ``write_path``
            (``<name>_stats.png``). Default True.

    Returns:
        label_map (nd array): The label map that was written.
    """

    if maxima_algorithm not in MAXIMA_ALGORITHMS:
        raise ValueError(f"Invalid maxima_algorithm: {maxima_algorithm}. Choose one of {', '.join(MAXIMA_ALGORITHMS)}.")
    if sigma is None:
        sigma = 0.75 if maxima_algorithm == "h_maxima" else 2.0
    if compactness is None:
        compactness = 0.0 if maxima_algorithm == "h_maxima" else 0.01

    img = tif.imread(input_path)
    if img.ndim not in (2, 3):
        raise ValueError(f"The image must be 2D or 3D, but it has {img.ndim} dimensions.")

    am_mask = img == 1
    if not am_mask.any():
        raise ValueError("The image contains no active material (label 1).")

    label_map = _watershed_label_map(am_mask, maxima_algorithm, h, sigma, compactness, min_distance)
    label_map = _label_unmarked_regions(am_mask, label_map)
    label_map, _, _ = segmentation.relabel_sequential(label_map)
    check_label_map(am_mask, label_map)

    n_particles = int(label_map.max())
    label_map = label_map.astype(_label_dtype(n_particles))
    # minisblack: a stack of greyscale slices, also when the first axis has length 3 or 4 (which tifffile would otherwise store as RGB)
    tif.imwrite(write_path, label_map, photometric="minisblack")

    sizes = np.bincount(label_map.ravel())[1:]
    diameters = _equivalent_diameters(sizes, label_map.ndim)
    print(f"Labelled {n_particles} particles. Equivalent diameter (voxels): median {np.median(diameters):.1f}, "
          f"min {diameters.min():.1f}, max {diameters.max():.1f}.")

    base = os.path.splitext(write_path)[0]
    if save_image:
        _save_label_map_image(label_map, base + "_slices.png")
    if save_stats:
        _save_size_distribution(diameters, label_map.ndim, base + "_stats.png")

    return label_map


def check_label_map(am_mask, label_map):
    """
    Checks that a label map is valid for an electrode image, in one pass over the image.

    Every AM voxel must be labelled, only AM voxels may be labelled, and each particle must be a
    single connected region (face connectivity, as used to build the OpenFOAM mesh).

    Args:
        am_mask (nd array): True where the electrode image is active material.
        label_map (nd array): The particle IDs (0 outside the AM).

    Returns:
    """

    if np.any(am_mask & (label_map == 0)):
        raise ValueError("Some AM voxels were not labelled.")
    if np.any(~am_mask & (label_map > 0)):
        raise ValueError("Some voxels outside the AM were labelled.")

    struct = ndi.generate_binary_structure(label_map.ndim, 1)
    for i, region in enumerate(ndi.find_objects(label_map), start=1):
        if region is None:
            continue
        n_components = ndi.label(label_map[region] == i, structure=struct)[1]
        if n_components > 1:
            raise ValueError(f"Particle {i} is fragmented into {n_components} components.")


def _watershed_label_map(am_mask, maxima_algorithm, h, sigma, compactness, min_distance):
    # distance of each AM voxel to the nearest non-AM voxel, kept in float32 to save memory
    distance = ndi.distance_transform_edt(am_mask).astype(np.float32)
    if sigma > 0:
        distance = ndi.gaussian_filter(distance, sigma=sigma)

    if maxima_algorithm == "h_maxima":
        peaks = morphology.h_maxima(distance, h).astype(bool) & am_mask
        markers = measure.label(peaks)
    elif maxima_algorithm == "local_maxima":
        markers = measure.label(morphology.local_maxima(distance) & am_mask)
    else:
        from skimage.feature import peak_local_max
        # keep peaks near the image border: particles cut by the image edge are normal in electrode images
        coords = peak_local_max(distance, labels=am_mask, min_distance=min_distance, exclude_border=False)
        if len(coords) == 0:
            raise ValueError("peak_local_max found no peaks. Try a smaller min_distance or sigma.")
        markers = np.zeros(distance.shape, dtype=np.int32)
        markers[tuple(coords.T)] = np.arange(1, len(coords) + 1)

    return segmentation.watershed(-distance, markers, mask=am_mask, compactness=compactness)


def _label_unmarked_regions(am_mask, label_map):
    # The watershed labels every connected AM region that contains a marker. Regions without a marker
    # (for example very small particles with no peak high enough) are separate from all labelled
    # particles, so each becomes a particle of its own.
    unlabelled = am_mask & (label_map == 0)
    if not unlabelled.any():
        return label_map
    struct = ndi.generate_binary_structure(label_map.ndim, 1)
    regions, n = ndi.label(unlabelled, structure=struct)
    label_map = label_map.astype(np.int64 if label_map.max() + n >= 2**31 else np.int32, copy=True)
    label_map[regions > 0] = regions[regions > 0] + label_map.max()
    return label_map


def _label_dtype(n_particles):
    return np.uint16 if n_particles <= np.iinfo(np.uint16).max else np.uint32


def _equivalent_diameters(sizes, ndim):
    # diameter of the sphere (3D) or circle (2D) with the same number of voxels, in voxels
    sizes = np.asarray(sizes, dtype=float)
    if ndim == 3:
        return (6 * sizes / np.pi) ** (1 / 3)
    return (4 * sizes / np.pi) ** 0.5


def _label_colours(n_particles):
    from matplotlib.colors import ListedColormap
    # random but repeatable colours, so neighbouring particles are easy to tell apart; background white
    rng = np.random.default_rng(0)
    colours = np.ones((n_particles + 1, 3))
    colours[1:] = 0.15 + 0.75 * rng.random((n_particles, 3))
    return ListedColormap(colours)


def _save_label_map_image(label_map, path):
    from matplotlib.figure import Figure

    n_particles = int(label_map.max())
    cmap = _label_colours(n_particles)
    style = dict(cmap=cmap, vmin=0, vmax=max(n_particles, 1), interpolation="nearest")

    if label_map.ndim == 2:
        fig = Figure(figsize=(6, 6), layout="constrained")
        ax = fig.add_subplot()
        ax.imshow(label_map, **style)
        ax.set_title(f"Label map ({n_particles} particles)")
        ax.set_xlabel("axis 1")
        ax.set_ylabel("axis 0 (x)")
    else:
        nx = label_map.shape[0]
        if nx < 4:
            warnings.warn(f"The image is only {nx} voxels long along x (axis 0), so no label map image was saved.",
                          UserWarning, stacklevel=3)
            return
        positions = [min(nx - 1, int((k + 0.5) * nx / 4)) for k in range(4)]
        fig = Figure(figsize=(10, 10), layout="constrained")
        axes = fig.subplots(2, 2)
        for ax, x in zip(axes.ravel(), positions):
            ax.imshow(label_map[x], **style)
            ax.set_title(f"x = {x} (of {nx})")
            ax.set_xlabel("axis 2")
            ax.set_ylabel("axis 1")
        fig.suptitle(f"Label map: slices along x ({n_particles} particles)")
    fig.savefig(path, dpi=150)


def _save_size_distribution(diameters, ndim, path):
    from matplotlib.figure import Figure

    n_particles = len(diameters)
    shape = "sphere" if ndim == 3 else "circle"
    fig = Figure(figsize=(7, 4.5), layout="constrained")
    ax = fig.add_subplot()
    bins = min(50, max(5, int(np.sqrt(n_particles)) + 1))
    ax.hist(diameters, bins=bins, color="#4C72B0", edgecolor="white")
    ax.set_xlabel(f"Equivalent {shape} diameter (voxels)")
    ax.set_ylabel("Number of particles")
    ax.set_title(f"Particle size distribution ({n_particles} particles)")
    summary = (f"particles: {n_particles}\n"
               f"median: {np.median(diameters):.1f}\n"
               f"mean: {np.mean(diameters):.1f}\n"
               f"min: {np.min(diameters):.1f}\n"
               f"max: {np.max(diameters):.1f}")
    ax.text(0.98, 0.97, summary, transform=ax.transAxes, ha="right", va="top", family="monospace",
            bbox=dict(boxstyle="round", facecolor="white", edgecolor="0.7"))
    fig.savefig(path, dpi=150)
