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
3. A TIF image of their electrode structure. Three phases are allowed
   – electrolyte as label 0, active material (AM) labelled 1, and carbon-binder
   domain (CBD) labelled 2. 

A label map identifying the different AM particles within the electrode
image is also recommended. However, a function is provided with the
package to generate this if needed.

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
