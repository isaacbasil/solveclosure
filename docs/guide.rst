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
2. An OpenFOAM installation. 
3. A TIF image of their electrode structure, using the labels below.

===== =====================================================
Label Phase
===== =====================================================
0     Electrolyte
1     Active material (AM)
2     Carbon-binder domain (CBD)
3     Separator (optional, see `Separators`_)
51    Inactive material (optional, see `Inactive Material`_)
===== =====================================================

A label map identifying the different AM particles within the electrode
image is also recommended. However, a function is provided with the
package to generate this if needed.

Separators
----------

Where active material touches the separator, the reaction is reduced by the
separator surface porosity, :math:`\varepsilon_{\mathrm{sep}}^{\mathrm{surf}}`,
set with the ``sep_surf_por`` argument (default 1, meaning no reduction).
Mark the separator by labelling its voxels 3. Only the boundary between AM and
separator voxels matters, so a separator layer one voxel thick is enough.
As for the CBD, the AM-separator area, weighted by the surface porosity, is
included in the particle surface area :math:`A_{i}` of the volumetric source
term. Faces of the image that are not labelled are treated as walls with no
flux.

If your image does not include the separator, ``add_separator_layer`` adds a
layer of separator voxels to one face of the image and pads the label map to
match:

.. code-block:: python

   import tifffile
   import solveclosure

   img = tifffile.imread("electrode_image.tif")
   label_map = tifffile.imread("label_map.tif")

   img, label_map = solveclosure.add_separator_layer(img, label_map, axis=0, side="start")

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
-----------------

Voxels labelled 51 are inactive material, for example particles that are no
longer electrochemically active. Inactive material completely blocks the
active material surface it touches: there is no reaction and no flux there,
so those faces are not part of the particle surface area :math:`A_{i}` and
have a zero-gradient boundary condition. This is the same as a separator with
a surface porosity of 0.

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
  size distribution, as equivalent sphere (or circle) diameters in voxels.

Particles that touch along a large, flat contact, with no narrowing between
them, cannot be separated from their shape alone. Check the slices, and use a
label map from your image processing software for important datasets if
needed. The label map must start at 1, have the same shape as the image, and
each particle must be one connected region; ``solveclosure.check_label_map``
checks this.

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
   \partial_{t}s_{i}^{t} & =D_{k}\Delta s_{i}^{t}+\frac{1}{F}\frac{A_{i}}{V_{k_{i}}} & \textrm{in }\Omega_{k_{i}},\\
   -\boldsymbol{n}\cdot D_{k}\nabla s_{i}^{t} & =\frac{1}{F} & \textrm{at }\partial\Omega_{k_{i},e},\\
   \boldsymbol{n}\cdot\nabla s_{i}^{t} & =-\varepsilon_{\mathrm{cbd}}^{\mathrm{surf}}\frac{1}{FD_{k}} & \textrm{at }\partial\Omega_{k_{i},\mathrm{cbd}},\\
   \boldsymbol{n}\cdot\nabla s_{i}^{t} & =-\varepsilon_{\mathrm{sep}}^{\mathrm{surf}}\frac{1}{FD_{k}} & \textrm{at }\partial\Omega_{k_{i},\mathrm{sep}},\\
   \boldsymbol{n}\cdot\nabla s_{i}^{t} & =\boldsymbol{n}\cdot\nabla s_{j}^{t} & \textrm{at }\partial\Omega_{k_{i},k_{j}},\\
   s_{i}^{t} & =s_{j}^{t} & \textrm{at }\partial\Omega_{k_{i},k_{j}},\\
   s_{i}^{t} & =0 & \textrm{at }t=0.
   \end{aligned}

Option 2
~~~~~~~~

This PDE is solved if the ``allow_flux`` argument is set to ``False``.

.. math::

   \begin{aligned}
   \partial_{t}s_{i}^{t} & =D_{k}\Delta s_{i}^{t}+\frac{1}{F}\frac{A_{i}}{V_{k_{i}}} & \textrm{in }\Omega_{k_{i}},\\
   -\boldsymbol{n}\cdot D_{k}\nabla s_{i}^{t} & =\frac{1}{F} & \textrm{at }\partial\Omega_{k_{i},e},\\
   \boldsymbol{n}\cdot\nabla s_{i}^{t} & =-\varepsilon_{\mathrm{cbd}}^{\mathrm{surf}}\frac{1}{FD_{k}} & \textrm{at }\partial\Omega_{k_{i},\mathrm{cbd}},\\
   \boldsymbol{n}\cdot\nabla s_{i}^{t} & =-\varepsilon_{\mathrm{sep}}^{\mathrm{surf}}\frac{1}{FD_{k}} & \textrm{at }\partial\Omega_{k_{i},\mathrm{sep}},\\
   \boldsymbol{n}\cdot\nabla s_{i}^{t} & =0 & \textrm{at }\partial\Omega_{k_{i},k_{j}},\\
   s_{i}^{t} & =0 & \textrm{at }t=0.
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
   \partial_{\hat{t}}\hat{s}_{i}^{t} & =\hat{\Delta}\hat{s}_{i}^{t}+\frac{LA_{i}}{V_{k_{i}}} & \textrm{in }\Omega_{k_{i}},\\
   \boldsymbol{n}\cdot\hat{\nabla}\hat{s}_{i}^{t} & =-1 & \textrm{at }\partial\Omega_{k_{i},e},\\
   \boldsymbol{n}\cdot\hat{\nabla}\hat{s}_{i}^{t} & =-\varepsilon_{\mathrm{cbd}}^{\mathrm{surf}} & \textrm{at }\partial\Omega_{k_{i},\mathrm{cbd}},\\
   \boldsymbol{n}\cdot\hat{\nabla}\hat{s}_{i}^{t} & =-\varepsilon_{\mathrm{sep}}^{\mathrm{surf}} & \textrm{at }\partial\Omega_{k_{i},\mathrm{sep}},\\
   \boldsymbol{n}\cdot\hat{\nabla}\hat{s}_{i}^{t} & =\boldsymbol{n}\cdot\hat{\nabla}\hat{s}_{j}^{t} & \textrm{at }\partial\Omega_{k_{i},k_{j}},\\
   \hat{s}_{i}^{t} & =\hat{s}_{j}^{t} & \textrm{at }\partial\Omega_{k_{i},k_{j}},\\
   \hat{s}_{i}^{t} & =0 & \textrm{at }\hat{t}=0.
   \end{aligned}

Option 2 is non-dimensionalised in the same way.

Solution of the PDEs
--------------------

The Solver
~~~~~~~~~~

The closure problem is solved for all particles together in a single
OpenFOAM case, with each particle as its own region. Both options of the
closure problem PDE are supported, selected with the ``allow_flux``
argument.

We use OpenFOAM's ``chtMultiRegionFoam`` solver.
Although originally designed for transient fluid flow and solid heat conduction,
the PDEs for the latter take the same form as our closure problem.

Due to the solver being intended for fluid dynamics, we employ several
workarounds. For example, the solver computes a temperature (``T``) field,
and enforces that ``T`` cannot be negative. In our problem, no such constraint
exists — the closure variable will generally be negative.
Therefore, we use a ``T offset`` (a large constant added to initial condition,
and subtracted in post-processing). 

Simulation Time
~~~~~~~~~~~~~~~

The closure problem is transient, and the result is taken at steady state, so
the solver must run long enough to reach it. The end time is set with the
``end_time`` argument of ``solve_closure``. By default it is

- :math:`\hat{t} = 0.25` for a dimensionless case, and
- :math:`t = (\textrm{image length along axis 0})^{2}/(4D_{k})` for a
  dimensional case, which is the same physical time when :math:`L` is the
  image length.

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
four continuations); in that case a warning is shown. To stop at ``end_time``
regardless, set ``continue_to_steady_state=False``; a warning is still shown
if steady state was not reached. The end time that was
reached and the number of continuations are saved in ``closure_data.pickle``
under ``end time`` and ``continuations``.

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

Template directories are contained within the repository, which are
used to set up the OpenFOAM case. 

Managing Results
----------------

Important outputs from the simulations are stored within the
``closure_data.pickle`` file, saved inside the case directory that you provide.

Most importantly, this contains the surface average of the closure
variable under the keys:

- ``global s surface average transient``  
- ``global s surface average steady``  

To look at the microscale fields. you can open the ``case.foam`` file within the OpenFOAM case using Paraview. 
The closure variable field is called ``T``, since OpenFOAM is normally solving for temperature.

Reprocessing results
~~~~~~~~~~~~~~~~~~~~

``solve_closure`` processes the results automatically. If you rerun the
OpenFOAM solver yourself, process the results again with:

.. code-block:: python

   solveclosure.process_closure_results(case_dir)

The settings of the case (``dimensionless``, ``L`` and the CBD and separator
surface porosities) are read from ``closure_data.pickle``, so they always
match the solved case. Cases set up with solveclosure 0.1.0 do not save these
settings. To reprocess one of them, add the values that were used for the
solve first:

.. code-block:: python

   import pickle

   path = "case_dir/closure_data.pickle"
   with open(path, "rb") as f:
       closure_data = pickle.load(f)

   closure_data.update({
       "dimensionless": True,          # as used for the solve
       "L": 1e-5,                      # lengthscale in m (None for a dimensional case)
       "cbd surface porosity": 0.5,
       "sep surface porosity": 1.0,
   })

   with open(path, "wb") as f:
       pickle.dump(closure_data, f)

Running on a High-Performance Computer (HPC)
--------------------------------------------

By default, the closure problem will be solved locally on a single core.
The solver can be parallelised on your local machine by using the
``parallelise`` argument. For large cases, it may be necessary to use a HPC,
to access more cores and/or memory. 

You should first copy the template ``sbatch_launch_script`` from the templates
directory. This gives an outline of a script for a HPC that uses Slurm. 
Modify:

1. The ``#SBATCH --partition`` command. Contact your system administrator if unsure what to put here.  
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

* Ensure the number of processors in your sbatch launch script matches
  that in your python launch script. 

* Ensure that the python package is accessible by the HPC nodes (your virtual
  environment may not exist on the HPC). Contact your system administrator to
  do this.  
