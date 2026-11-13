# Snapshot tests of the OpenFOAM case files written by solve_closure. No OpenFOAM needed.
#
# Small cases are set up with stand-ins for the OpenFOAM tools (run_solver=False), and every file
# solveclosure writes is compared with a stored copy in tests/snapshots. This catches unintended
# changes to the case files. When a change is intended, update the stored copies with
#
#   SOLVECLOSURE_UPDATE_SNAPSHOTS=1 pytest tests/test_snapshots.py
#
# and check the differences (git diff tests/snapshots) before committing them.

import json
import os
import pickle
import shutil

import numpy as np
import pytest
import tifffile

import solveclosure

SNAPSHOT_DIR = os.path.join(os.path.dirname(__file__), "snapshots")
UPDATE = os.environ.get("SOLVECLOSURE_UPDATE_SNAPSHOTS") == "1"

# stand-ins for the OpenFOAM tools called while the case is set up
FAKE_TOOLS = {
    "foamListTimes": "#!/bin/bash\nexit 0\n",
    "blockMesh": "#!/bin/bash\nexit 0\n",
    "topoSet": "#!/bin/bash\nexit 0\n",
    "decomposePar": "#!/bin/bash\nexit 0\n",
    # splitMeshRegions: create the folders of every region named in topoSetDict
    "splitMeshRegions": """#!/bin/bash
while [ $# -gt 0 ]; do [ "$1" = "-case" ] && case_dir="$2"; shift; done
for r in $(grep -B2 "cellZoneSet" "$case_dir/system/topoSetDict" | awk '/name/{gsub(";","",$2); print $2}'); do
  mkdir -p "$case_dir/0/$r" "$case_dir/constant/$r" "$case_dir/system/$r"
done
""",
}

CASES = {
    # every phase: two particles, electrolyte, CBD, separator and inactive material
    "all_phases_dimensionless": dict(cbd_surf_por=0.5, sep_surf_por=0.3),
    "option_2_dimensional_parallel": dict(cbd_surf_por=0.5, sep_surf_por=0.3, dimensionless=False, D_s=4e-14,
                                          allow_flux=False, parallelise=True, n_procs=2),
}


@pytest.fixture
def fake_openfoam(tmp_path):
    bin_dir = tmp_path / "fake_openfoam"
    bin_dir.mkdir()
    for name, script in FAKE_TOOLS.items():
        path = bin_dir / name
        path.write_text(script)
        path.chmod(0o755)
    return f"export PATH={bin_dir}:$PATH"


def small_image():
    img = np.zeros((8, 6, 4), dtype=np.uint8)
    label_map = np.zeros(img.shape, dtype=np.uint16)
    img[1:4, 1:5, :] = 1
    label_map[1:4, 1:5, :] = 1
    img[4:7, 2:5, 1:3] = 1
    label_map[4:7, 2:5, 1:3] = 2
    img[0, :, :] = 3          # separator
    img[1:4, 0, :] = 2        # CBD
    img[7, :, :] = 51         # inactive material
    return img, label_map


def case_files(case_dir):
    # the text files solveclosure writes, and a readable summary of closure_data.pickle
    files = {}
    for root, _, names in os.walk(case_dir):
        for name in names:
            path = os.path.join(root, name)
            rel = os.path.relpath(path, case_dir)
            if name.startswith("log.") or name.endswith((".pickle", ".tif")):
                continue
            with open(path) as f:
                files[rel] = f.read()
    with open(os.path.join(case_dir, "closure_data.pickle"), "rb") as f:
        data = pickle.load(f)
    files["closure_data.json"] = json.dumps(data, indent=1, sort_keys=True, default=repr) + "\n"
    return files


@pytest.mark.parametrize("name", sorted(CASES))
def test_case_files_match_snapshot(tmp_path, fake_openfoam, name):
    img, label_map = small_image()
    img_path, label_map_path = str(tmp_path / "img.tif"), str(tmp_path / "lab.tif")
    tifffile.imwrite(img_path, img)
    tifffile.imwrite(label_map_path, label_map)
    case_dir = str(tmp_path / "case")
    solveclosure.solve_closure(case_dir, img_path, label_map_path, 1e-7, run_solver=False,
                               load_of_cmd=fake_openfoam, **CASES[name])
    files = case_files(case_dir)

    snapshot = os.path.join(SNAPSHOT_DIR, name)
    if UPDATE:
        shutil.rmtree(snapshot, ignore_errors=True)
        for rel, text in files.items():
            os.makedirs(os.path.dirname(os.path.join(snapshot, rel)), exist_ok=True)
            with open(os.path.join(snapshot, rel), "w") as f:
                f.write(text)
        pytest.skip("snapshot updated")

    assert os.path.isdir(snapshot), f"No snapshot for {name}; run with SOLVECLOSURE_UPDATE_SNAPSHOTS=1"
    stored = case_files_from_snapshot(snapshot)
    assert sorted(files) == sorted(stored), "The set of case files has changed"
    for rel in sorted(files):
        assert files[rel] == stored[rel], f"{rel} differs from the snapshot"


def case_files_from_snapshot(snapshot):
    files = {}
    for root, _, names in os.walk(snapshot):
        for name in names:
            path = os.path.join(root, name)
            with open(path) as f:
                files[os.path.relpath(path, snapshot)] = f.read()
    return files
