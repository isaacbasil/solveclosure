# solve2eqclosure

Solves the closure problem for the 2-equation model published by Paten et. al

## 🚀 Installing solve2eqclosure

solve2eqclosure is available on GNU/Linux.
It is recommended to install solve2eqclosure into a virtual environement. 

### Using pip

```bash
pip install pybamm
```


## 💻 Using solve2eqclosure

The simplest form of script to run solve2eqclosure: 

```python
import solve2eqclosure

img_path = "electrode_image.tif" # the path to your electrode image, electrolyte labelled as 0, active material 1, and CBD 2. 
label_map_path = "label_map.tif" # to path to a label map of active material particles (beginning at 1).

case_dir = "case_dir/" # am empty directory where OpenFOAM cases will be built. 

load_of_cmd = "source /usr/lib/openfoam/openfoam2412/etc/bashrc" # the command specific for your system to load an OpenFOAM terminal.

voxel = 1e-7 # the electrode image voxel size in meters.

cbd_surface_porosity = 1.0 # the surface porosity of CBD. Set to 1 if CBD is not present. 

D_s = 4e-14 # the diffusivity of active material in m2.s-1.


solve2eqclosure.solve_closure_multiparticle(case_dir, img_path, label_map_path, load_of_cmd, voxel, cbd_surface_porosity, D_s)

```
