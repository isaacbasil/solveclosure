# Makes the geometry images of the examples shown on the Examples page:
#   two_squares_geometry.png and three_particles_geometry.png
# Run from this folder: python make_geometry_images.py
import numpy as np
import tifffile
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from skimage.measure import marching_cubes

import solveclosure


def surface(ax, solid, el, az):
    # the surface of the active material, shaded by its angle to a light along the view direction
    verts, faces, *_ = marching_cubes(np.pad(solid, 1).astype(float), 0.5)
    verts -= 1                      # image axes 0, 1, 2 are x, y, z
    v = verts[faces]
    normals = -np.cross(v[:, 1] - v[:, 0], v[:, 2] - v[:, 0])    # pointing out of the solid
    normals /= np.linalg.norm(normals, axis=1)[:, None] + 1e-12
    e, a = np.radians(el), np.radians(az)
    light = np.array([np.cos(e) * np.cos(a), np.cos(e) * np.sin(a), np.sin(e)])
    shade = 0.35 + 0.65 * np.clip(normals @ light, 0, 1)
    mesh = Poly3DCollection(v, linewidths=0)
    mesh.set_facecolor(np.c_[np.outer(shade, [0.85, 0.52, 0.25]), np.ones(len(shade))])
    ax.add_collection3d(mesh)
    ax.view_init(el, az)
    ax.set_xlabel("x"); ax.set_ylabel("y"); ax.set_zlabel("z")


# three particles: three views
img = tifffile.imread(solveclosure.example_path("three_particles.tif"))
solid = img == 1
n = img.shape[0]
views = [(25, 120, "Oblique"), (90, -90, "Top (along z)"), (0, 0, "Side (along x)")]
fig = plt.figure(figsize=(15, 5.2))
for k, (el, az, title) in enumerate(views):
    ax = fig.add_subplot(1, 3, k + 1, projection="3d")
    surface(ax, solid, el, az)
    ax.set_xlim(0, n); ax.set_ylim(0, n); ax.set_zlim(0, n)
    ax.set_box_aspect((1, 1, 1))
    ax.set_title(title)
fig.suptitle(f"Active material (label 1), {n}×{n}×{n} voxels, solid fraction {solid.mean():.2f}")
plt.tight_layout(); fig.subplots_adjust(top=0.86)
fig.savefig("three_particles_geometry.png", dpi=150)

# two squares: a slice (the image is the same through its thickness)
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch

img = tifffile.imread(solveclosure.example_path("two_squares.tif"))
nx, ny, nz = img.shape
colours = ["#f2f2f2", (0.85, 0.52, 0.25)]    # electrolyte, active material
fig, ax = plt.subplots(figsize=(5.5, 5.2))
ax.imshow(img[:, :, nz // 2].T, origin="lower", cmap=ListedColormap(colours), vmin=0, vmax=1,
          extent=(0, nx, 0, ny), interpolation="nearest")
ax.set_xlabel("x"); ax.set_ylabel("y")
ax.set_title(f"Slice through the image ({nx}×{ny}×{nz} voxels),\nthe same at every z")
ax.legend(handles=[Patch(color=colours[1], label="active material (1)"),
                   Patch(facecolor=colours[0], edgecolor="0.6", label="electrolyte (0)")],
          loc="upper left", fontsize=9)
plt.tight_layout()
fig.savefig("two_squares_geometry.png", dpi=150)
