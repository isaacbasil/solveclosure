import numpy as np

# Labels accepted in the electrode image.
ALLOWED_LABELS = {
    0: "electrolyte",
    1: "active material (AM)",
    2: "carbon-binder domain (CBD)",
    3: "separator",
    51: "inactive material (blocks the AM surface it touches)",
}


def check_image_labels(img, label_map):
    """
    Checks that the electrode image only contains supported labels and that the label map matches its shape.

    Args:
        img (nd array): The electrode image.
        label_map (nd array): The map of particle IDs.

    Returns:
    """

    if img.shape != label_map.shape:
        raise ValueError(f"The image {img.shape} and the label map {label_map.shape} must have the same shape.")

    present = set(np.unique(img).astype(int).tolist())
    unknown = sorted(present - set(ALLOWED_LABELS))
    if unknown:
        allowed = ", ".join(f"{k} ({v})" for k, v in ALLOWED_LABELS.items())
        raise ValueError(f"The image contains unsupported label(s) {unknown}. Allowed labels are: {allowed}.")
