# Tests for write_bc_file. These do not need OpenFOAM and run in milliseconds.

import re

import pytest

from solveclosure.openfoam_case_setup import write_bc_file


def patches(path):
    """The patch names and their BC types in a T file."""
    text = open(path).read()
    return dict(re.findall(r"^    (\w+)\s*\n    \{\s*\n\s*type\s+([\w:]+);", text, re.M))


@pytest.mark.parametrize("allow_flux, coupled_type", [(True, "compressible::turbulentTemperatureRadCoupledMixed"),
                                                      (False, "zeroGradient")])
def test_only_the_particles_own_neighbours_are_written(tmp_path, allow_flux, coupled_type):
    path = str(tmp_path / "T")
    write_bc_file(path, "particle_2", -1.0, -0.5, False, [1, 5, "elec", "cbd"], 300, allow_flux=allow_flux)
    p = patches(path)

    assert {k: v for k, v in p.items() if "_to_particle_" in k} == {"particle_2_to_particle_1": coupled_type,
                                                                    "particle_2_to_particle_5": coupled_type}
    assert p["particle_2_to_Elec"] == "fixedGradient" and p["particle_2_to_CBD"] == "fixedGradient"
    assert "particle_2_to_Sep" not in p and "particle_2_to_Inactive" not in p


def test_inactive_neighbour_gives_a_zero_flux_patch(tmp_path):
    path = str(tmp_path / "T")
    write_bc_file(path, "particle_1", -1.0, False, False, ["elec", "inactive"], 300)
    p = patches(path)
    assert p["particle_1_to_Inactive"] == "zeroGradient"
    assert not [k for k in p if "_to_particle_" in k]
