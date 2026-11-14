# Changelog

All notable changes to solveclosure are listed here. The documentation is at
https://solveclosure.readthedocs.io.

## 0.2.0

This release changes the interface of the main functions. Scripts written for 0.1.0 need
updating; see "Changed (breaking)" below.

### Added

- Dimensionless solves (`dimensionless=True`, the default): the result depends only on the
  geometry, `D_s` is not needed, and the lengthscale is set with `L` (default: the image length
  along axis 0). Dimensional solves are still available with `dimensionless=False` and `D_s`.
- Separators (label 3): the reaction at the AM-separator boundary is scaled by the separator
  surface porosity `sep_surf_por`. `add_separator_layer` adds a separator layer to one face of an
  image.
- Inactive material (label 51) now blocks the AM surface it touches (no reaction and no flux). In
  0.1.0 it was treated as electrolyte, so results change for images that contain label 51.
- Automatic continuation to steady state: after `end_time`, the solver is continued (end time
  doubled each time) until the global surface average varies by less than 0.1% over the last half
  of the run, or `max_end_time` is reached. New options `end_time`, `write_interval`,
  `continue_to_steady_state` and `max_end_time` (0.1.0 always stopped at 800 s).
- `surface_average.png`, a plot of the corrected surface average against time, saved in the case
  directory (`save_plot=True`).
- `overwrite` option: an existing case in `case_dir` is only replaced with `overwrite=True`; the
  case directory is created if it does not exist.
- `solver_settings_dir` option, to use your own OpenFOAM `fvSchemes` and `fvSolution`.
- `closure_data.pickle` saves the case settings (`dimensionless`, `L`, `voxel`, surface porosities,
  end time, write interval, number of continuations), so `process_closure_results(case_dir)` needs
  no other arguments.
- `generate_label_map`: h-maxima markers (`maxima_algorithm="h_maxima"`, the new default, with `h`),
  as well as `"local_maxima"` and `"peak_local_max"`; 2D images; `save_image` (slices of the label
  map) and `save_stats` (particle count and size distribution) pngs; much faster checks for large
  images; uint32 label maps above 65535 particles.
- `check_label_map`, to check a label map against its electrode image.
- Example images installed with the package, and `example_path` to find them; a three particles
  example that generates its label map.
- Documentation on Read the Docs: installation, OpenFOAM set-up, quick start, input files, allowed
  phases, the PDEs, dimensionless and dimensional solves, simulation time, solver settings, the
  results (including the corrected surface average), HPC, citing, an Examples page and the API.
- Tests (unit, snapshot, analytical, Option 2, serial and parallel, examples) and GitHub Actions.

### Changed (breaking)

- `solve_closure_multiparticle` is renamed `solve_closure`. The old name is kept as an alias, with
  a deprecation warning, and will be removed in a future release. Calls written for 0.1.0 still
  need their arguments updated as described below.
- The per-particle solve mode is removed; all particles are solved together in one case.
- Optional arguments of `solve_closure`, `process_closure_results`, `generate_label_map` and
  `add_separator_layer` are keyword-only. `cbd_surf_por` and `D_s` are no longer positional:
  `solve_closure(case_dir, img_path, label_map_path, voxel, cbd_surf_por=..., D_s=..., dimensionless=False)`.
- The default is now a dimensionless solve; pass `dimensionless=False` and `D_s` for the
  dimensional results of 0.1.0.
- `cbd_surf_por` and `sep_surf_por` are only needed when the image contains CBD or separator: an
  error is raised if one is missing, a warning is shown if one is given for a phase that is not in
  the image, and `None` is saved when it does not apply.
- `process_closure_results(case_dir)` reads the case settings from `closure_data.pickle`; its other
  arguments are removed. It now returns the closure data.
- `generate_label_map`: `show_image` is replaced by `save_image` and `save_stats`; the default
  markers, `sigma` and `compactness` changed with the new h-maxima default.
- An existing case in `case_dir` raises an error instead of asking to continue (y/n); pass
  `overwrite=True` to replace it.
- The default `T_offset` is 10 for dimensionless and 1e5 for dimensional solves.
- The `method` key is no longer saved in `closure_data.pickle`.
- If no OpenFOAM installation is found, an error is raised instead of exiting Python.
- Python 3.10 or later is required (0.1.0 allowed 3.8).

### Changed

- Boundary condition files list only each particle's own neighbours, so case files are much
  smaller for images with many particles. Results are unchanged.
- `imagecodecs` is a dependency, so compressed TIF images can be read.
- The example images are installed with the package instead of being in the `examples` folder.
- `CITATION.CFF` is renamed `CITATION.cff` and follows the Citation File Format 1.2.0.

## 0.1.0

First release.
