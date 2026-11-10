# solveclosure

[![Documentation Status](https://readthedocs.org/projects/solveclosure/badge/?version=latest)](https://solveclosure.readthedocs.io/en/latest/)

📖 **Documentation:** https://solveclosure.readthedocs.io

Solves the closure problem for the dual-continuum model published by Paten et. al. See the following two articles for more information: 

https://doi.org/10.1149/1945-7111/ae335f
https://doi.org/10.1149/1945-7111/ae3527

## 🚀 Installing solveclosure

solveclosure is available on GNU/Linux.
It is recommended to install solveclosure into a virtual environement. 

### Using pip

```bash
pip install solveclosure
```


## 💻 Using solveclosure

The simplest form of script to run solveclosure: 

```python
import solveclosure

img_path = "electrode_image.tif" # the path to your electrode image, electrolyte labelled as 0, active material 1, and CBD 2. 
label_map_path = "label_map.tif" # the path to a label map of active material particles (beginning at 1).

case_dir = "case_dir/" # an empty directory where OpenFOAM cases will be built. 

load_of_cmd = "source /usr/lib/openfoam/openfoam2412/etc/bashrc" # the command specific for your system to load an OpenFOAM terminal.

voxel = 1e-7 # the electrode image voxel size in meters.

cbd_surface_porosity = 1.0 # the surface porosity of CBD. Set to 1 if CBD is not present. 

D_s = 4e-14 # the diffusivity of active material in m2.s-1.


solveclosure.solve_closure_multiparticle(
    case_dir,
    img_path,
    label_map_path,
    voxel,
    cbd_surface_porosity,
    dimensionless=False, # solve the dimensional problem, using D_s
    D_s=D_s,
    load_of_cmd=load_of_cmd, # optional: if omitted, solveclosure searches for an OpenFOAM installation
)

```
