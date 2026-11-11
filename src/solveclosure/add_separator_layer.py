import numpy as np

SEPARATOR_LABEL = 3


def add_separator_layer(img, label_map, axis=0, side="start", thickness=1):
    """
    Adds a layer of separator voxels (label 3) to one face of an electrode image.

    The image is padded, so no existing voxels are overwritten: active material on that face
    of the original image will touch the separator. The label map is padded with zeros to keep
    the two arrays the same shape.

    Note that padding changes the size of the image along ``axis``. In a dimensionless case, the
    default lengthscale ``L`` (the length of axis 0) then includes the separator layer; pass ``L`` to
    :func:`solveclosure.solve_closure` if you want a different value. The lengthscale used is saved
    in the results. Padding at the start of axis 0 also shifts the particle centre x positions by
    ``thickness`` voxels.

    Args:
        img (nd array): The electrode image (electrolyte 0, AM 1, CBD 2).
        label_map (nd array): The map of particle IDs, with the same shape as ``img``.
        axis (int): The axis normal to the separator face (0, 1 or 2). Default 0.
        side (str): "start" to add the layer before index 0 of ``axis``, or "end" to add it after the last index. Default "start".
        thickness (int): The number of voxel layers to add. Default 1.

    Returns:
        img_out (nd array): The image with the separator layer added.
        label_map_out (nd array): The label map padded with zeros to match.
    """

    img = np.asarray(img)
    label_map = np.asarray(label_map)

    if img.shape != label_map.shape:
        raise ValueError(f"The image {img.shape} and the label map {label_map.shape} must have the same shape.")
    if img.ndim != 3:
        raise ValueError("The image must be 3D.")
    if axis not in (0, 1, 2):
        raise ValueError("axis must be 0, 1 or 2.")
    if side not in ("start", "end"):
        raise ValueError('side must be "start" or "end".')
    if int(thickness) != thickness or thickness < 1:
        raise ValueError("thickness must be a positive integer.")

    if img.dtype == bool:
        img = img.astype(np.uint8)

    pad = [(0, 0), (0, 0), (0, 0)]
    pad[axis] = (int(thickness), 0) if side == "start" else (0, int(thickness))

    img_out = np.pad(img, pad, mode="constant", constant_values=SEPARATOR_LABEL)
    label_map_out = np.pad(label_map, pad, mode="constant", constant_values=0)

    return img_out, label_map_out
