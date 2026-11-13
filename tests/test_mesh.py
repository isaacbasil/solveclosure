# Checks that the OpenFOAM mesh puts the right voxels in each particle region, by comparing the
# cell centres of each region, as computed by OpenFOAM, with the label map.

import os
import re
import subprocess
import sys

import numpy as np
import pytest
import tifffile

import solveclosure


def read_cell_centres(path):
    # internalField of a volVectorField written by OpenFOAM (binary or ascii)
    data = open(path, "rb").read()
    m = re.search(rb"internalField\s+nonuniform\s+List<vector>\s*(\d+)\s*\(", data)
    n = int(m.group(1))
    start = m.end()
    if b"format      binary" in data[:1000]:
        return np.frombuffer(data[start:start + 24 * n], dtype="<f8").reshape(n, 3)
    values = re.findall(rb"\(([^()]+)\)", data[start:])[:n]
    return np.array([[float(v) for v in triple.split()] for triple in values])


@pytest.mark.openfoam
def test_particle_regions_contain_the_voxels_of_their_particle(tmp_path):
    # an asymmetric image, so a wrong cell numbering would put the wrong voxels in a region
    img = np.zeros((5, 4, 3), dtype=np.uint8)
    label_map = np.zeros(img.shape, dtype=np.uint16)
    img[0:2, 0:3, 0:2] = 1
    label_map[0:2, 0:3, 0:2] = 1
    img[3:5, 1:4, 1:3] = 1
    label_map[3:5, 1:4, 1:3] = 2
    img[2, 0, :] = 2    # some CBD
    img_path, label_map_path = str(tmp_path / "img.tif"), str(tmp_path / "lab.tif")
    tifffile.imwrite(img_path, img)
    tifffile.imwrite(label_map_path, label_map)

    voxel = 1e-7
    case_dir = str(tmp_path / "case")
    solveclosure.solve_closure(case_dir, img_path, label_map_path, voxel, cbd_surf_por=0.5, dimensionless=False,
                               D_s=1e-14, run_solver=False)

    from conftest import LOAD_OF_CMD
    load_of_cmd = LOAD_OF_CMD or sys.modules["solveclosure.solve_closure"].find_latest_openfoam_installation()
    of_case = os.path.join(case_dir, "openfoam_case")
    for particle in (1, 2):
        cmd = f"{load_of_cmd} && postProcess -case {of_case} -region particle_{particle} -func writeCellCentres -time 0"
        subprocess.run(["bash", "-c", cmd], check=True, capture_output=True)
        centres = read_cell_centres(os.path.join(of_case, "0", f"particle_{particle}", "C"))
        voxels = sorted(map(tuple, np.floor(centres / voxel).astype(int).tolist()))
        expected = sorted(map(tuple, np.argwhere(label_map == particle).tolist()))
        assert voxels == expected
