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

Option 1
~~~~~~~~

This PDE is solved if the ``allow_flux`` argument is set to ``False``.

.. math::

   \begin{aligned}
   \partial_{t}s_{i}^{t} & = D_{k}\Delta s_{i}^{t}+H(t)\frac{1}{F}\frac{A_{i}}{V_{k_{i}}} && \text{in } \Omega_{k_{i}}^{\mathrm{micro}}, \\
   -\mathbf{n}\cdot D_{k}\nabla s_{i}^{t} & = H(t)\frac{1}{F} && \text{at } \partial\Omega_{k_{i},e}^{\mathrm{in}}, \\
   \mathbf{n}\cdot\nabla s_{i} & = 0 && \text{at } \partial\Omega_{k_{i},k_{j}}^{\mathrm{in}}, \\
   s_{i}^{t} & = 0 && \text{at } t=0.
   \end{aligned}

Option 2
~~~~~~~~

This PDE is solved if the ``allow_flux`` argument is set to ``True``,
which is the default.

.. math::

   \begin{aligned}
   \partial_{t}s_{i}^{t} & = D_{k}\Delta s_{i}^{t}+H(t)\frac{1}{F}\frac{A_{i}}{V_{k_{i}}} && \text{in } \Omega_{k_{i}}^{\mathrm{micro}}, \\
   -\mathbf{n}\cdot D_{k}\nabla s_{i}^{t} & = H(t)\frac{1}{F} && \text{at } \partial\Omega_{k_{i},e}^{\mathrm{in}}, \\
   \mathbf{n}\cdot\nabla s_{i} & = \mathbf{n}\cdot\nabla s_{j} && \text{at } \partial\Omega_{k_{i},k_{j}}, \\
   s_{i} & = s_{j} && \text{at } \partial\Omega_{k_{i},k_{j}}.
   \end{aligned}

Dimensionless Form
~~~~~~~~~~~~~~~~~~

The closure problem can be non-dimensionalised using the following
dimensionless groups, which removes the dependency on :math:`D_{k}` and
thus the problem solely depends on electrode geometry.

.. math::

   \begin{aligned}
   s_{i} & = \frac{L^{2}}{D_{k}F}\frac{A_{i}}{V_{k_{i}}}\hat{s_{i}}, \\
   x & = \hat{x}L.
   \end{aligned}

For Option 1, this gives

.. math::

   \begin{aligned}
   \hat{\Delta}\hat{s_{i}} & = -1 && \text{in } \Omega_{k_{i}}^{\mathrm{micro}}, \\
   \mathbf{n}\cdot\hat{\nabla}\hat{s_{i}} & = -\frac{V_{k_{i}}}{A_{i}L} && \text{at } \partial\Omega_{k_{i},e}^{\mathrm{in}}, \\
   \mathbf{n}\cdot\nabla\hat{s_{i}} & = 0 && \text{at } \partial\Omega_{k_{i},k_{j}}^{\mathrm{in}}.
   \end{aligned}

Solution of the PDEs
--------------------

Case Type
~~~~~~~~~

The closure problem can be solved in ``multiparticle`` or ``per particle``
mode. In general, multiparticle mode is recommended – it is better
maintained, uses a more robust solver, and allows for both options
of the closure problem PDE. Per particle mode is mainly for very large
cases. It exploits the form of the PDE in Option 1 to solve the closure
problem for each particle independently, and thus scales very well with
mesh size. Therefore, only Option 1 is supported for per particle cases. 

The Solvers
~~~~~~~~~~~

For multiparticle cases, we use OpenFOAM's ``chtMultiRegionFoam`` solver.
Although originally designed for transient fluid flow and solid heat conduction,
the PDEs for the latter take the same form as our closure problem.

Due to the solver being intended for fluid dynamics, we employ several
workarounds. For example, the solver computes a temperature (``T``) field,
and enforces that ``T`` cannot be negative. In our problem, no such constraint
exists — the closure variable will generally be negative.
Therefore, we use a ``T offset`` (a large constant added to initial condition,
and subtracted in post-processing). 

For a per-particle case, ``laplacianFoam`` is used, which does not require
a ``T offset``.

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

Running on a High-Performance Computer (HPC)
--------------------------------------------

By default, the closure problem will be solved locally on a single core.
The solver can be parallelised on your local machine by using the
``parallelise`` argument. For large cases, it may be necessary to use a HPC,
to access more cores and/or memory. 

You should first copy the template ``sbatch_launch_script`` from the templates
directory. This gives an outline of a script for a HPC that uses Slurm. 
Modify:

1. The ``#SBATCH --partition`` command.  
2. The path to activate your virtual environment.  
3. The number of processors you want to use.  
4. The path to your python launch script.  

The python launch script should run ``solveclosure`` almost identically to
how you would run it locally, but you must provide the command to load
OpenFOAM, e.g.::

   module load openfoam/2006_220610

Checklist:

* Make sure your sbatch launch script is executable:

  .. code-block:: bash

     chmod +x sbatch_launch_script.sh

* Ensure the number of processors in your sbatch launch script matches
  that in your python launch script. 
