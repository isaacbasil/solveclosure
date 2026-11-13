# Tests for the simulation end time, the write interval and the steady state check.

import os
import pickle
import re
import warnings

import numpy as np
import pytest

import solveclosure
from solveclosure.process_closure_results import check_steady_state
from solveclosure.utility import load_openfoam_data, merge_postprocessing_time_folders

DEMO_PATH = os.path.dirname(solveclosure.example_path("two_squares.tif"))
IMG = os.path.join(DEMO_PATH, "two_squares.tif")
LABEL_MAP = os.path.join(DEMO_PATH, "two_squares_label_map.tif")
VOXEL = 1e-7
D_S = 4e-14
F = 96485


def solve(tmp_path, name, **kwargs):
    case_dir = os.path.join(str(tmp_path), name) + "/"
    os.makedirs(case_dir)
    solveclosure.solve_closure(case_dir, IMG, LABEL_MAP, VOXEL, **kwargs)
    with open(os.path.join(case_dir, "closure_data.pickle"), "rb") as f:
        return case_dir, pickle.load(f)


# ---------- quick checks (no OpenFOAM needed)

def test_check_steady_state():
    t = np.linspace(0, 1, 1001)
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        assert check_steady_state(t, -(1 - np.exp(-50 * t))) < 1e-3       # converged: no warning
    with pytest.warns(UserWarning, match="not reached steady state"):
        check_steady_state(t, -(1 - np.exp(-2 * t)))                       # still changing


def test_check_steady_state_not_fooled_by_overshoot():
    # like the surface average: overshoots by about 1%, then relaxes to -1
    t = np.linspace(0, 1, 2001)
    s = -1 + np.exp(-30 * t) * (1 - 0.4 * 30 * t)   # overshoots to about -1.012 at t = 0.117
    peak = t[np.argmin(s)]
    stop = t <= peak * 1.05            # stopped just after the peak, where the curve is flat
    assert abs(s[stop][-1] + 1) > 5e-3  # still about 1% from the steady value
    with pytest.warns(UserWarning, match="not reached steady state"):
        check_steady_state(t[stop], s[stop])


def test_merge_postprocessing_time_folders(tmp_path):
    fo = tmp_path / "postProcessing" / "particle_1" / "particle_1_volumeIntegral"
    for folder, rows in {"0": [(0.1, 1.0), (0.2, 2.0), (0.3, 3.0)],
                         "0.3": [(0.4, 4.0), (0.5, 5.0)],
                         "0.45": [(0.5, 5.5), (0.6, 6.0)]}.items():   # restarted from an earlier time
        (fo / folder).mkdir(parents=True)
        (fo / folder / "volFieldValue.dat").write_text("# header\n# Time  volIntegrate(T)\n" + "".join(f"{t}\t{v}\n" for t, v in rows))

    assert merge_postprocessing_time_folders(str(tmp_path)) == 1
    assert sorted(p.name for p in fo.iterdir()) == ["0"]
    t, v = load_openfoam_data(str(fo / "0" / "volFieldValue.dat"))
    assert t == [0.1, 0.2, 0.3, 0.4, 0.5, 0.6] and v == [1.0, 2.0, 3.0, 4.0, 5.5, 6.0]
    assert (fo / "0" / "volFieldValue.dat").read_text().startswith("# header\n# Time")
    assert merge_postprocessing_time_folders(str(tmp_path)) == 0     # nothing left to merge


# ---------- with OpenFOAM

def test_end_time_and_write_interval_are_used(tmp_path):
    case_dir, data = solve(tmp_path, "settings", dimensionless=True, end_time=0.3, write_interval=0.05, run_solver=False)
    with open(os.path.join(case_dir, "openfoam_case", "system", "controlDict")) as f:
        control = f.read()
    assert re.search(r"^endTime\s+0\.3;", control, re.M)
    assert re.search(r"^writeInterval\s+0\.05;", control, re.M)
    assert data["end time"] == 0.3 and data["write interval"] == 0.05


def test_default_end_times(tmp_path):
    _, dimless = solve(tmp_path, "dimless", dimensionless=True, run_solver=False)
    _, dim = solve(tmp_path, "dim", dimensionless=False, D_s=D_S, run_solver=False)
    image_length = 100 * VOXEL
    assert dimless["end time"] == 0.25
    assert dim["end time"] == pytest.approx(image_length ** 2 / (4 * D_S))  # same physical time as t_hat = 0.25
    assert dimless["write interval"] == 0.0625 and dim["write interval"] == pytest.approx(dim["end time"] / 4)


def test_dimensional_matches_dimensionless(tmp_path):
    _, dim = solve(tmp_path, "dim", dimensionless=False, D_s=D_S)
    _, dimless = solve(tmp_path, "dimless", dimensionless=True)
    L = dimless["L"]
    # s = L / (D_s F) * s_hat
    assert dim["global s surface average steady"] == pytest.approx(L / (D_S * F) * dimless["global s surface average steady"], rel=1e-5)


def test_short_end_time_warns_without_continuation(tmp_path):
    # t_hat = 0.0056 was the default in solveclosure 0.1.0 and stops long before steady state
    with pytest.warns(UserWarning, match="not reached steady state"):
        _, data = solve(tmp_path, "short", dimensionless=True, end_time=0.0056, max_end_time=0.0056)
    assert data["continuations"] == 0


def test_continue_to_steady_state_false_stops_at_end_time(tmp_path):
    with pytest.warns(UserWarning, match="not reached steady state"):
        case_dir, data = solve(tmp_path, "no_continue", dimensionless=True, end_time=0.02, continue_to_steady_state=False,
                               save_plot=False)
    assert data["continuations"] == 0 and data["end time"] == 0.02
    assert not os.path.exists(os.path.join(case_dir, "surface_average.png"))
    assert data["times for transient data"][-1] == pytest.approx(0.02)


def test_solver_is_continued_until_steady_state(tmp_path):
    with warnings.catch_warnings():
        warnings.simplefilter("error", UserWarning)   # no steady state warning expected
        case_dir, data = solve(tmp_path, "continued", dimensionless=True, end_time=0.02)
    # 0.02 -> 0.04 -> 0.08 -> 0.16 -> 0.32
    assert data["continuations"] == 4 and data["end time"] == pytest.approx(0.32)
    # same as one long run (-0.0659544, t_hat = 1), well within the 0.1% steady state tolerance
    assert data["global s surface average steady"] == pytest.approx(-0.0659544, rel=1e-4)
    t = np.asarray(data["times for transient data"])
    assert t[-1] == pytest.approx(0.32) and np.all(np.diff(t) > 0)          # one continuous transient
    pp = os.path.join(case_dir, "openfoam_case", "postProcessing", "particle_1", "particle_1_volumeIntegral")
    assert os.listdir(pp) == ["0"]
    assert os.path.isfile(os.path.join(case_dir, "surface_average.png"))   # saved by default


# ---------- surface average plot (no OpenFOAM needed)

def _closure_data(dimensionless, continuations, steady):
    t = np.linspace(0.01, 1.0, 200)
    s = -0.066 * (1 - np.exp(-t / (0.05 if steady else 0.8)))
    return {"times for transient data": t, "global s surface average transient": s,
            "global s surface average steady": s[-1], "dimensionless": dimensionless,
            "end time": 1.0, "continuations": continuations}


@pytest.mark.parametrize("dimensionless, continuations, steady", [(True, 0, True), (False, 2, False)])
def test_save_surface_average_plot(tmp_path, dimensionless, continuations, steady):
    from solveclosure.utility import save_surface_average_plot
    path = str(tmp_path / "surface_average.png")
    save_surface_average_plot(_closure_data(dimensionless, continuations, steady), path)
    assert os.path.getsize(path) > 10000
