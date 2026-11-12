# Tests for generate_label_map. These do not need OpenFOAM and run in seconds.

import os
import warnings

import numpy as np
import pytest
import tifffile
from scipy import ndimage as ndi

import solveclosure
from solveclosure.generate_label_map import check_label_map, _label_dtype

DEMO_PATH = os.path.join(os.path.dirname(__file__), "..", "examples", "two_squares")


def make_packing(n=96, n_spheres=150, rmin=5, rmax=11, overlap=0.8, seed=0):
    """Electrode-like packing of overlapping spheres, with the true particle of each voxel.

    Spheres may overlap, but their centres stay at least overlap * (r1 + r2) apart, so touching
    particles have a neck. Voxels in an overlap belong to the sphere with the lowest power distance.
    """
    rng = np.random.default_rng(seed)
    centres, radii = [], []
    for _ in range(100000):
        if len(centres) == n_spheres:
            break
        r = rng.uniform(rmin, rmax)
        c = rng.uniform(0, n, size=3)
        if all(np.linalg.norm(c - c2) >= overlap * (r + r2) for c2, r2 in zip(centres, radii)):
            centres.append(c)
            radii.append(r)
    z, y, x = np.ogrid[:n, :n, :n]
    best = np.full((n, n, n), np.inf, dtype=np.float32)
    true = np.zeros((n, n, n), dtype=np.int32)
    for i, (c, r) in enumerate(zip(centres, radii), start=1):
        d2 = ((z - c[0]) ** 2 + (y - c[1]) ** 2 + (x - c[2]) ** 2).astype(np.float32)
        take = (d2 <= r * r) & (d2 - r * r < best)
        best[take] = (d2 - r * r)[take]
        true[take] = i
    return (true > 0).astype(np.uint8), true


def fraction_recovered(true, pred, min_overlap=0.75):
    """Fraction of true particles matched by one predicted particle (intersection over union >= min_overlap)."""
    t, p = true.ravel(), pred.ravel().astype(np.int64)
    m = t > 0
    pairs, counts = np.unique(np.stack([t[m], p[m]]), axis=1, return_counts=True)
    t_size, p_size = np.bincount(t), np.bincount(p)
    best = np.zeros(t.max() + 1)
    for (ti, pi), c in zip(pairs.T, counts):
        if pi:
            best[ti] = max(best[ti], c / (t_size[ti] + p_size[pi] - c))
    present = np.unique(t[m])
    return np.mean(best[present] >= min_overlap)


def write(tmp_path, name, img):
    path = os.path.join(str(tmp_path), name)
    tifffile.imwrite(path, img, photometric="minisblack")
    return path


# ---------- accuracy

def test_recovers_particles_of_a_packing(tmp_path):
    img, true = make_packing()
    lab = solveclosure.generate_label_map(write(tmp_path, "img.tif", img), os.path.join(str(tmp_path), "lab.tif"),
                                          save_image=False, save_stats=False)
    assert fraction_recovered(true, lab) >= 0.9


def test_label_map_is_valid_and_written(tmp_path):
    img, _ = make_packing(n=64, n_spheres=60)
    out = os.path.join(str(tmp_path), "lab.tif")
    lab = solveclosure.generate_label_map(write(tmp_path, "img.tif", img), out)
    written = tifffile.imread(out)
    assert np.array_equal(written, lab) and written.dtype == np.uint16
    check_label_map(img == 1, lab)
    assert sorted(np.unique(lab)) == list(range(lab.max() + 1))  # IDs 1..N without gaps
    assert os.path.isfile(os.path.join(str(tmp_path), "lab_slices.png"))
    assert os.path.isfile(os.path.join(str(tmp_path), "lab_stats.png"))


def test_small_particle_without_peak_gets_its_own_label(tmp_path):
    img = np.zeros((20, 20, 20), dtype=np.uint8)
    img[3:15, 3:15, 3:15] = 1      # a cube
    img[18, 18, 18] = 1            # an isolated single voxel: no peak high enough for h-maxima
    lab = solveclosure.generate_label_map(write(tmp_path, "img.tif", img), os.path.join(str(tmp_path), "lab.tif"),
                                          save_image=False, save_stats=False)
    assert lab.max() == 2 and lab[18, 18, 18] > 0 and lab[18, 18, 18] != lab[8, 8, 8]


# ---------- other algorithms

@pytest.mark.parametrize("algorithm", ["local_maxima", "peak_local_max"])
def test_other_algorithms_give_valid_label_maps(tmp_path, algorithm):
    img, true = make_packing(n=64, n_spheres=60)
    lab = solveclosure.generate_label_map(write(tmp_path, "img.tif", img), os.path.join(str(tmp_path), "lab.tif"),
                                          maxima_algorithm=algorithm, save_image=False, save_stats=False)
    check_label_map(img == 1, lab)
    assert fraction_recovered(true, lab) >= 0.6


def test_peak_local_max_on_a_thin_image(tmp_path):
    # used to crash: peaks within min_distance of the border were excluded, leaving none
    out = os.path.join(str(tmp_path), "lab.tif")
    lab = solveclosure.generate_label_map(os.path.join(DEMO_PATH, "two_squares.tif"), out,
                                          maxima_algorithm="peak_local_max", save_image=False, save_stats=False)
    assert lab.max() >= 1


def test_invalid_algorithm(tmp_path):
    with pytest.raises(ValueError, match="Invalid maxima_algorithm"):
        solveclosure.generate_label_map(os.path.join(DEMO_PATH, "two_squares.tif"), os.path.join(str(tmp_path), "lab.tif"),
                                        maxima_algorithm="nope")


# ---------- 2D and thin images

def test_2d_image(tmp_path):
    img, _ = make_packing(n=64, n_spheres=60)
    out = os.path.join(str(tmp_path), "lab.tif")
    lab = solveclosure.generate_label_map(write(tmp_path, "img.tif", img[32]), out)
    assert lab.ndim == 2 and lab.max() > 1
    check_label_map(img[32] == 1, lab)
    assert os.path.isfile(os.path.join(str(tmp_path), "lab_slices.png"))
    assert os.path.isfile(os.path.join(str(tmp_path), "lab_stats.png"))


def test_thin_3d_image_warns_and_saves_no_slices(tmp_path):
    img, _ = make_packing(n=64, n_spheres=60)
    out = os.path.join(str(tmp_path), "lab.tif")
    with pytest.warns(UserWarning, match="no label map image was saved"):
        solveclosure.generate_label_map(write(tmp_path, "img.tif", img[:3]), out)
    assert not os.path.exists(os.path.join(str(tmp_path), "lab_slices.png"))
    assert os.path.isfile(os.path.join(str(tmp_path), "lab_stats.png"))


def test_no_pngs_when_switched_off(tmp_path):
    img, _ = make_packing(n=64, n_spheres=60)
    solveclosure.generate_label_map(write(tmp_path, "img.tif", img), os.path.join(str(tmp_path), "lab.tif"),
                                    save_image=False, save_stats=False)
    assert not [f for f in os.listdir(str(tmp_path)) if f.endswith(".png")]


# ---------- checks and data type

def test_check_label_map_catches_problems():
    am = np.zeros((6, 6, 6), dtype=bool)
    am[1:5, 1:5, 1:5] = True
    good = am.astype(np.int32)
    check_label_map(am, good)

    unlabelled = good.copy(); unlabelled[2, 2, 2] = 0
    with pytest.raises(ValueError, match="not labelled"):
        check_label_map(am, unlabelled)

    outside = good.copy(); outside[0, 0, 0] = 1
    with pytest.raises(ValueError, match="outside the AM"):
        check_label_map(am, outside)

    fragmented = good.copy(); fragmented[1:5, 1:5, 2] = 2   # a wall of particle 2 cuts particle 1 in two
    with pytest.raises(ValueError, match="Particle 1 is fragmented"):
        check_label_map(am, fragmented)


def test_label_dtype():
    assert _label_dtype(65535) == np.uint16
    assert _label_dtype(65536) == np.uint32   # more particles than uint16 can hold
