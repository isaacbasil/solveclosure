User Guide
==========

Introduction
------------

This package solves the closure problem presented in the work by Paten
et al. OpenFOAM is used to solve the partial differential equation
(PDE) on an electrode microstructure, which is input by the user in
the form of a TIF image. Two options for the closure problem PDE are
provided in the article, described below.

Prerequisites
-------------

The user must have:

1. A Linux system. If using Windows, this can be done easily using Windows
   Subsystem for Linux (WSL). The package may work on Mac, but it has
   not been tested.
2. An OpenFOAM installation from openfoam.com (see `OpenFOAM`_).
3. A TIF image of their electrode structure, and a label map of its
   particles (see `Input Files`_). If you do not have a label map, it can be
   generated with ``generate_label_map`` (see `Generating a Label Map`_).

Installation
------------

solveclosure needs Python 3.8 or later. Install it from PyPI, preferably in a
virtual environment:

.. code-block:: bash

   python3 -m venv venv
   source venv/bin/activate
   pip install solveclosure

OpenFOAM
~~~~~~~~

solveclosure uses the OpenFOAM version from openfoam.com (ESI-OpenCFD). It has
been tested with v2006 and v2412. Older versions may not work: v1912, as
packaged by Ubuntu, failed in our tests. The OpenFOAM Foundation version
(openfoam.org) has not been tested.

On Ubuntu, including Ubuntu on WSL, a precompiled OpenFOAM can be installed
with the commands below. See https://dl.openfoam.com for other systems.

.. code-block:: bash

   curl -s https://dl.openfoam.com/add-debian-repo.sh | sudo bash
   sudo apt-get update
   sudo apt-get install openfoam2412-default

solveclosure finds your OpenFOAM installation automatically: it looks for
folders named ``openfoam*`` in ``/opt``, ``/usr/lib/openfoam`` and
``/usr/local``, picks the last one in alphabetical order and loads OpenFOAM by
sourcing its ``etc/bashrc``. This finds the installation above.

If OpenFOAM is installed somewhere else, or if several versions are installed,
give the command that loads OpenFOAM with the ``load_of_cmd`` argument of
``solve_closure``. solveclosure runs this command in ``bash`` before each
OpenFOAM tool. For example:

.. code-block:: python

   load_of_cmd = "source /usr/lib/openfoam/openfoam2412/etc/bashrc"

On computers that use environment modules, such as most HPCs, it is usually a
``module load`` command (see `Running on a High-Performance Computer (HPC)`_).
If no installation is found and ``load_of_cmd`` is not given, an error is
raised.

Quick Start
-----------

The two squares example is a small case: an image of 100 × 100 × 10 voxels of
0.1 µm, with two touching active material particles in electrolyte. The
particles have square cross-sections of 40 × 40 and 20 × 20 voxels and run
through the whole thickness of the image. The example files are in the
solveclosure repository, so first clone it:

.. code-block:: bash

   git clone https://github.com/isaacbasil/solveclosure.git
   cd solveclosure

Then run, from the ``solveclosure`` folder:

.. code-block:: python

   import solveclosure

   solveclosure.solve_closure(
       "two_squares_case",                               # case_dir
       "examples/two_squares/two_squares.tif",           # electrode image
       "examples/two_squares/two_squares_label_map.tif", # label map
       1e-7,                                             # voxel size (m)
       load_of_cmd="source /usr/lib/openfoam/openfoam2412/etc/bashrc",
   )

This solves the dimensionless closure problem (the default). The case is built
in ``two_squares_case``, which is created if it does not exist. When the solver
has finished, this folder contains:

- ``closure_data.pickle``, with the results (see `Managing Results`_). The
  steady corrected surface average, ``global s surface average steady``, is
  -0.06595.
- ``surface_average.png``, a plot of the surface average against time.
- ``openfoam_case``, the OpenFOAM case, which can be opened in ParaView to 
  view the closure variable fields.

To solve the dimensional problem instead, add ``dimensionless=False`` and
``D_s=4e-14`` (the diffusivity in m\ :sup:`2` s\ :sup:`-1`). The result is then
-170.9 mol s C\ :sup:`-1` m\ :sup:`-1` (see
`Dimensionless or Dimensional Solve`_).
``examples/two_squares/solve_closure_example.py`` runs this dimensional case,
in a folder called ``two_squares_case``.

If ``case_dir`` already contains a case, ``solve_closure`` stops with an error.
Delete the existing case, or pass ``overwrite=True`` to replace it.

Input Files
-----------

``solve_closure`` needs two 3D TIF images of the same shape:

- the electrode image, in which each voxel is labelled with its phase (see
  `Allowed Phases`_), and
- the label map, which gives each active material particle its own ID. Every
  AM voxel has the ID of its particle, and all other voxels are 0. The IDs
  must run from 1 to the number of particles without gaps, and each particle
  must be a single connected region (voxels connected through their faces).

The voxels must be cubes, with the side length given by the ``voxel``
argument, in metres. Axis 0 of the images is the x direction: the default
lengthscale ``L`` is the length of the image along axis 0, and the particle
centre x positions in the results are measured along it.

``solveclosure.check_label_map(img == 1, label_map)`` checks a label map
against its electrode image. To create a label map, see
`Generating a Label Map`_.

Allowed Phases
--------------

Each voxel of the electrode image is labelled with the phase it belongs to:

===== ==============================================================
Label Phase
===== ==============================================================
0     Electrolyte
1     Active material (AM)
2     Carbon-binder domain (optional, see `Carbon-Binder Domain`_)
3     Separator (optional, see `Separator`_)
51    Inactive material (optional, see `Inactive Material`_)
===== ==============================================================

The phases that the AM touches set the reacting surface area of each particle,
which appears in the volumetric source term of the closure problem (see
`The PDEs`_). For particle :math:`i`, it is

.. math::

   A_{i} = A_{i,e}
   + \varepsilon_{\mathrm{cbd}}^{\mathrm{surf}} A_{i,\mathrm{cbd}}
   + \varepsilon_{\mathrm{sep}}^{\mathrm{surf}} A_{i,\mathrm{sep}},

where :math:`A_{i,e}`, :math:`A_{i,\mathrm{cbd}}` and
:math:`A_{i,\mathrm{sep}}` are the areas of the boundaries between particle
:math:`i` and the electrolyte, the CBD and the separator, and
:math:`\varepsilon_{\mathrm{cbd}}^{\mathrm{surf}}` and
:math:`\varepsilon_{\mathrm{sep}}^{\mathrm{surf}}` are the CBD and separator
surface porosities. The boundaries with other particles, with inactive
material and with the faces of the image do not react, so they are not part
of :math:`A_{i}`. The faces of the image are walls with no flux.

Carbon-Binder Domain
~~~~~~~~~~~~~~~~~~~~

Where the AM touches the carbon-binder domain (CBD), the reaction is reduced by
the CBD surface porosity, :math:`\varepsilon_{\mathrm{cbd}}^{\mathrm{surf}}`,
set with the ``cbd_surf_por`` argument. A value of 1 means that the CBD does
not hinder the reaction (the same as electrolyte), and 0 means that it blocks
the reaction completely.

Separator
~~~~~~~~~

Where the AM touches the separator, the reaction is reduced by the separator
surface porosity, :math:`\varepsilon_{\mathrm{sep}}^{\mathrm{surf}}`, set with
the ``sep_surf_por`` argument, in the same way as for the CBD. Mark the
separator by labelling its voxels 3. Only the boundary between AM and
separator voxels matters, so a separator layer one voxel thick is enough.

If your image does not include the separator, ``add_separator_layer`` adds a
layer of separator voxels to one face of the image and pads the label map to
match:

.. code-block:: python

   import tifffile
   import solveclosure

   img = tifffile.imread("electrode_image.tif")
   label_map = tifffile.imread("label_map.tif")

   img, label_map = solveclosure.add_separator_layer(
       img, label_map, axis=0, side="start"
   )

   tifffile.imwrite("electrode_image_with_separator.tif", img)
   tifffile.imwrite("label_map_with_separator.tif", label_map)

Padding makes the image larger. In a dimensionless case, the default
lengthscale ``L`` is the length of axis 0 of the image, so it includes the
separator layer; pass ``L`` explicitly if you want a different value. The
lengthscale used is saved in the results under ``L``. Adding the layer at the
start of axis 0 also shifts the particle centre x positions stored in the
results by the thickness of the layer.

See ``examples/two_squares/solve_closure_separator_example.py`` for a complete
example.

Inactive Material
~~~~~~~~~~~~~~~~~

Voxels labelled 51 are inactive material, which some users may have in images
used for microscale simulations (to avoid isolated electrolyte regions).
Inactive material completely blocks the active material surface it touches:
there is no reaction and no flux there, so those faces are not part of the
particle surface area :math:`A_{i}` and have a zero-gradient boundary
condition.

Generating a Label Map
----------------------

``generate_label_map`` creates a label map from an electrode image, giving
each active material particle its own ID (starting at 1):

.. code-block:: python

   solveclosure.generate_label_map("electrode_image.tif", "label_map.tif")

It separates touching particles with a watershed on the distance map of the
active material, starting from one marker per peak of the distance map. By
default (``maxima_algorithm="h_maxima"``), only peaks that stand at least
``h = 0.75`` voxels above the lowest point between them and a higher peak are
used, so flat tops and small bumps of the distance map do not create extra
particles. Decrease ``h`` if particles are merged, and increase it if particles
are split. The methods of solveclosure 0.1.0 are available as
``maxima_algorithm="local_maxima"`` and ``"peak_local_max"``. 2D and 3D images
are supported.

Next to the label map, two images are saved for checking the result:

- ``<name>_slices.png`` (``save_image=True``): four slices of the label map,
  evenly spaced along x (axis 0), or the whole label map for a 2D image. For a
  3D image with fewer than 4 voxels along x, a warning is shown instead.
- ``<name>_stats.png`` (``save_stats=True``): the number of particles and their
  size distribution. The size of each particle is given as the diameter, in
  voxels, of a sphere with the same volume (or of a circle with the same area,
  for a 2D image).

Particles that touch along a large, flat contact, with no narrowing between
them, cannot be separated from their shape alone. Check the slices, and use a
label map from your image processing software for important datasets if
needed. The label map must meet the requirements in `Input Files`_.

The PDEs
--------

The notation follows the articles listed on the home page, which define
all of the symbols used below.

Option 1
~~~~~~~~

This PDE is solved if the ``allow_flux`` argument is set to ``True``,
which is the default,

.. math::

   \begin{aligned}
   \partial_{t}s_{i}^{t}
      & =D_{k}\Delta s_{i}^{t}+\frac{1}{F}\frac{A_{i}}{V_{k_{i}}}
      & \textrm{in }\Omega_{k_{i}},\\
   -\boldsymbol{n}\cdot D_{k}\nabla s_{i}^{t}
      & =\frac{1}{F}
      & \textrm{at }\partial\Omega_{k_{i},e},\\
   \boldsymbol{n}\cdot\nabla s_{i}^{t}
      & =-\varepsilon_{\mathrm{cbd}}^{\mathrm{surf}}\frac{1}{FD_{k}}
      & \textrm{at }\partial\Omega_{k_{i},\mathrm{cbd}},\\
   \boldsymbol{n}\cdot\nabla s_{i}^{t}
      & =-\varepsilon_{\mathrm{sep}}^{\mathrm{surf}}\frac{1}{FD_{k}}
      & \textrm{at }\partial\Omega_{k_{i},\mathrm{sep}},\\
   \boldsymbol{n}\cdot\nabla s_{i}^{t}
      & =\boldsymbol{n}\cdot\nabla s_{j}^{t}
      & \textrm{at }\partial\Omega_{k_{i},k_{j}},\\
   s_{i}^{t}
      & =s_{j}^{t}
      & \textrm{at }\partial\Omega_{k_{i},k_{j}},\\
   s_{i}^{t}
      & =0
      & \textrm{at }t=0.
   \end{aligned}

Option 2
~~~~~~~~

This PDE is solved if the ``allow_flux`` argument is set to ``False``.

.. math::

   \begin{aligned}
   \partial_{t}s_{i}^{t}
      & =D_{k}\Delta s_{i}^{t}+\frac{1}{F}\frac{A_{i}}{V_{k_{i}}}
      & \textrm{in }\Omega_{k_{i}},\\
   -\boldsymbol{n}\cdot D_{k}\nabla s_{i}^{t}
      & =\frac{1}{F}
      & \textrm{at }\partial\Omega_{k_{i},e},\\
   \boldsymbol{n}\cdot\nabla s_{i}^{t}
      & =-\varepsilon_{\mathrm{cbd}}^{\mathrm{surf}}\frac{1}{FD_{k}}
      & \textrm{at }\partial\Omega_{k_{i},\mathrm{cbd}},\\
   \boldsymbol{n}\cdot\nabla s_{i}^{t}
      & =-\varepsilon_{\mathrm{sep}}^{\mathrm{surf}}\frac{1}{FD_{k}}
      & \textrm{at }\partial\Omega_{k_{i},\mathrm{sep}},\\
   \boldsymbol{n}\cdot\nabla s_{i}^{t}
      & =0
      & \textrm{at }\partial\Omega_{k_{i},k_{j}},\\
   s_{i}^{t}
      & =0
      & \textrm{at }t=0.
   \end{aligned}

Dimensionless Form
~~~~~~~~~~~~~~~~~~

The closure problem can be non-dimensionalised using the following
dimensionless groups, which removes the dependency on :math:`D_{k}` and
thus the problem solely depends on electrode geometry.

.. math::

   \begin{aligned}
   s_{i}^{t} & = \frac{L}{D_{k}F}\hat{s}_{i}^{t}, \\
   x & = \hat{x}L, \\
   t & = \hat{t}\frac{L^{2}}{D_{k}}.
   \end{aligned}

For Option 1, this gives

.. math::

   \begin{aligned}
   \partial_{\hat{t}}\hat{s}_{i}^{t}
      & =\hat{\Delta}\hat{s}_{i}^{t}+\frac{LA_{i}}{V_{k_{i}}}
      & \textrm{in }\Omega_{k_{i}},\\
   \boldsymbol{n}\cdot\hat{\nabla}\hat{s}_{i}^{t}
      & =-1
      & \textrm{at }\partial\Omega_{k_{i},e},\\
   \boldsymbol{n}\cdot\hat{\nabla}\hat{s}_{i}^{t}
      & =-\varepsilon_{\mathrm{cbd}}^{\mathrm{surf}}
      & \textrm{at }\partial\Omega_{k_{i},\mathrm{cbd}},\\
   \boldsymbol{n}\cdot\hat{\nabla}\hat{s}_{i}^{t}
      & =-\varepsilon_{\mathrm{sep}}^{\mathrm{surf}}
      & \textrm{at }\partial\Omega_{k_{i},\mathrm{sep}},\\
   \boldsymbol{n}\cdot\hat{\nabla}\hat{s}_{i}^{t}
      & =\boldsymbol{n}\cdot\hat{\nabla}\hat{s}_{j}^{t}
      & \textrm{at }\partial\Omega_{k_{i},k_{j}},\\
   \hat{s}_{i}^{t}
      & =\hat{s}_{j}^{t}
      & \textrm{at }\partial\Omega_{k_{i},k_{j}},\\
   \hat{s}_{i}^{t}
      & =0
      & \textrm{at }\hat{t}=0.
   \end{aligned}

Option 2 is non-dimensionalised in the same way.

Dimensionless or Dimensional Solve
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

By default (``dimensionless=True``), ``solve_closure`` solves the dimensionless
problem above. The result depends only on the geometry, so one solve can be
used for any diffusivity :math:`D_{k}`, and ``D_s`` is not needed. The
lengthscale :math:`L` is set with the ``L`` argument, in metres. By default it
is the length of the image along axis 0 (number of voxels times ``voxel``).
The value used is saved in the results under ``L``.

The results of a dimensionless solve are :math:`\hat{s}` and :math:`\hat{t}`.
Convert them to dimensional values with the same :math:`L`:

.. math::

   s = \frac{L}{D_{k}F}\hat{s}, \qquad t = \frac{L^{2}}{D_{k}}\hat{t}.

With ``dimensionless=False``, the dimensional problem is solved directly, and
``D_s`` (:math:`D_{k}`, in m\ :sup:`2` s\ :sup:`-1`) must be given. The closure
variable :math:`s` is then in mol s C\ :sup:`-1` m\ :sup:`-1`, which is the
same as (mol m\ :sup:`-3`)/(A m\ :sup:`-2`). Times are in seconds.

Areas, volumes and positions in the results are always in SI units (m\
:sup:`2`, m\ :sup:`3` and m), whichever mode is used.

Solution of the PDEs
--------------------

The Solver
~~~~~~~~~~

The closure problem is solved for all particles together in a single
OpenFOAM case, with each particle as its own region. Both options of the
closure problem PDE are supported, selected with the ``allow_flux``
argument.

We use OpenFOAM's ``chtMultiRegionFoam`` solver. Although originally designed
for transient fluid flow and solid heat conduction, the PDEs for the latter
take the same form as our closure problem.

Due to the solver being intended for fluid dynamics, we employ several
workarounds. For example, the solver computes a temperature (``T``) field, and
enforces that ``T`` cannot be negative. In our problem, no such constraint
exists — the closure variable will generally be negative. Therefore, we use a
``T offset`` (a large constant added to initial condition, and subtracted in
post-processing).

Simulation Time
~~~~~~~~~~~~~~~

The closure problem is transient, and the result is taken at steady state, so
the solver must run long enough to reach it. The end time is set with the
``end_time`` argument of ``solve_closure``. By default it is

- :math:`\hat{t} = 0.25` for a dimensionless case, and
- :math:`t = (\textrm{image length along axis 0})^{2}/(4D_{k})` for a
  dimensional case.

This is enough for many cases. Larger connected networks of particles take
longer to settle (up to about :math:`\hat{t} = 1` for a network spanning the
whole image), and these are continued automatically, as described below.

After the solver finishes, solveclosure checks that the global surface
average has reached steady state: it must vary by less than 0.1% (maximum
minus minimum) over the last half of the simulation. The surface average
overshoots its steady value early in the simulation, and checking over the
last half of the run stops a run near that peak from being mistaken for a
steady one.

If steady state has not been reached, the solver is continued from where it
stopped, with the end time doubled, and the check is repeated. The time
stepping is unchanged, so the transient results are the same as for one
continuous run. This repeats until steady state is reached or the end time
would exceed ``max_end_time`` (default ``16 * end_time``, which allows up to
four continuations); in that case a warning is shown. To turn off this
automatic continuation feature, and force the solver to stop at ``end_time``,
set ``continue_to_steady_state=False``; a warning is still shown if steady
state was not reached. The end time that was reached and the number of
continuations are saved in ``closure_data.pickle`` under ``end time`` and
``continuations``.

When the solver is continued, OpenFOAM writes the surface and volume
integrals of the continuation to a new folder in ``postProcessing``, named
after the time it was continued from. solveclosure merges these back into the
files of the ``0`` folder, so the output looks like that of one continuous
simulation. If you continue a simulation yourself, do the same with
``solveclosure.utility.merge_postprocessing_time_folders`` before running
``process_closure_results``.

The ``write_interval`` argument sets how often the 3D fields are written, for
viewing in ParaView (default ``end_time / 4``, updated when the solver is
continued). It does not affect the results, because the surface and volume
integrals are recorded at every time step.

Template Directories
~~~~~~~~~~~~~~~~~~~~

Template directories are contained within the repository, which are used to set
up the OpenFOAM case.

Managing Results
----------------

Important outputs from the simulations are stored within the
``closure_data.pickle`` file, saved inside the case directory that you provide.
It is a Python dictionary:

.. code-block:: python

   import pickle

   with open("case_dir/closure_data.pickle", "rb") as f:
       closure_data = pickle.load(f)

   print(closure_data["global s surface average steady"])

Most importantly, this contains the surface average of the closure
variable under the keys:

- ``global s surface average transient``: at each time in
  ``times for transient data``
- ``global s surface average steady``: the value at the last time, once
  steady state has been reached

These are :math:`\hat{s}` for a dimensionless case and :math:`s` for a
dimensional one (see `Dimensionless or Dimensional Solve`_).

The corrected surface average
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Both keys hold the *corrected* surface average: the surface average of the
closure variable over all reacting AM surfaces (weighted by the CBD and
separator surface porosities), minus its volume average over all of the AM.

The closure problem has flux conditions on every boundary, so its solution is
only defined up to a constant, which is fixed by requiring a volume average of
zero. In theory, the volume average stays at zero during the simulation,
because the volume source term exactly balances the flux through the reacting
surfaces. In the simulation it can drift slightly away from zero; with Option 1
this mostly comes from the coupling of neighbouring particles, which are solved
as separate regions. Subtracting the volume average gives the surface average
of the solution with zero volume average, and removes this drift. For example,
in the two squares example the volume average drifts to about 1.6% of the
surface average. This drift can be reduced 17-fold by increasing the outer
correctors used by the solver from 1 to 3, but this adds computational cost,
and only changes the corrected surface average by 0.002% (showing that our
approach of subtracting the volume average is effective).

The uncorrected values can be recovered from the volume average:
``global s surface average steady`` + ``global s volume average final``.

Other results
~~~~~~~~~~~~~

``closure_data.pickle`` also contains:

- ``times for transient data``: the times of the transient data
  (:math:`\hat{t}`, or seconds for a dimensional case).
- ``global s volume average transient`` and ``global s volume average final``:
  the volume average of the closure variable over all of the AM, at each time
  and at the last time.
- ``total area (surface porosity included)``: the reacting AM surface area,
  with the AM-CBD and AM-separator areas weighted by their surface porosities
  (m\ :sup:`2`).
- ``am-elec area``, ``am-cbd area (surface porosity omitted)`` and
  ``am-sep area (surface porosity omitted)``: the area of each type of AM
  surface, without the surface porosities (m\ :sup:`2`).
- ``total particle volume``: the volume of all of the AM (m\ :sup:`3`).
- ``particle data``: a dictionary with one entry per particle ID, containing

  - ``particle surface area``: the reacting surface area of the particle, with
    surface porosities included (m\ :sup:`2`),
  - ``particle volume`` (m\ :sup:`3`),
  - ``centre x position``: the position of the particle's centre along axis 0
    (m),
  - ``s surf int transient``: the raw surface integral of the solver field over
    the particle's reacting surface. It includes the ``T offset`` (see
    `The Solver`_), and areas are in the units of the mesh (m\ :sup:`2` for a
    dimensional case, :math:`L^{2}` for a dimensionless one). To get the
    particle's surface average, divide by its surface area in the same units
    and subtract the ``T offset``.

The settings of the case are saved too: ``dimensionless``, ``L`` (m, or
``None`` for a dimensional case), ``voxel`` (m), ``cbd surface porosity`` and
``sep surface porosity`` (``None`` if that phase is not in the image and no
value was given), ``T offset``, ``end time`` (the time reached, including any
continuations), ``write interval``, ``continue to steady state``,
``max end time`` and ``continuations``.

``solve_closure`` also saves ``surface_average.png`` in the case directory
(``save_plot=True``, the default): the transient surface average against time,
with its steady value, the window used for the steady-state check and the
times at which the solver was continued.

To look at the microscale fields, you can open the ``case.foam`` file within
the OpenFOAM case using ParaView. The closure variable field is called ``T``,
since OpenFOAM is normally solving for temperature. Remember to subtract the
``T offset``.

Reprocessing results
~~~~~~~~~~~~~~~~~~~~

``solve_closure`` processes the results automatically. If you rerun the
OpenFOAM solver yourself, process the results again with:

.. code-block:: python

   solveclosure.process_closure_results(case_dir)

The settings of the case (``dimensionless``, ``L`` and the CBD and separator
surface porosities) are read from ``closure_data.pickle``, so they always match
the solved case.

Running on a High-Performance Computer (HPC)
--------------------------------------------

By default, the closure problem will be solved locally on a single core. The
solver can be parallelised on your local machine by using the ``parallelise``
argument, with ``n_procs`` processes (default 8). Use no more processes than
the computer has physical cores: with more, the solver becomes much slower
instead of faster. For large cases, it may be necessary to use a HPC, to access
more cores and/or memory.

You should first copy the template ``sbatch_launch_script.sh`` from the
``templates`` directory of the installed package. This command prints the
folder of the installed package, which contains ``templates``:

.. code-block:: bash

   python -c "import solveclosure; print(solveclosure.__path__[0])"

The template gives an outline of a script for a HPC that uses Slurm. Modify:

1. The ``#SBATCH --partition`` command. Contact your system administrator if
   unsure what to put here.
2. The path to activate your virtual environment.
3. The number of processors you want to use (the #SBATCH --ntasks argument).
4. The path to your python launch script.

The python launch script should run ``solveclosure`` almost identically to
how you would run it locally, but you must provide the command to load
OpenFOAM, e.g.::

   module load openfoam/2006_220610

Then, launch the job using::

   sbatch sbatch_launch_script.sh

Checklist:

* Make sure your sbatch launch script is executable:

  .. code-block:: bash

     chmod +x sbatch_launch_script.sh

* Ensure the number of processors in your sbatch launch script matches that in
  your python launch script.

* Ensure that the python package is accessible by the HPC nodes (your virtual
  environment may not exist on the HPC). Contact your system administrator to
  do this.

Citing solveclosure
-------------------

If you use solveclosure in your work, please cite the articles by Paten et al.:

* https://doi.org/10.1149/1945-7111/ae335f
* https://doi.org/10.1149/1945-7111/ae3527

and the software itself, archived on Zenodo:
https://doi.org/10.5281/zenodo.17558923. The citation details are also in the
``CITATION.cff`` file of the repository, from which GitHub generates its "Cite
this repository" button.
