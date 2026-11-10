API reference
=============

The functions most users need are available directly from the top-level
package:

* :func:`solveclosure.solve_closure_multiparticle` builds and solves the
  closure problem in OpenFOAM.
* :func:`solveclosure.process_closure_results` processes the results of a
  solved case.
* :func:`solveclosure.generate_label_map` generates a label map of the active
  material particles, if you do not already have one.

Full module listing
-------------------

These pages are generated automatically from the docstrings in the source
code each time the documentation is built.

.. autosummary::
   :toctree: generated
   :recursive:

   solveclosure
