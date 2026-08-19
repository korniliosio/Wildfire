# make_fig2_pipeline_diagram.py
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

OUT_PNG = "thesis/figures/fig2_preprocessing_pipeline.png"

def box(ax, xy, w, h, text, fontsize=10):
    x, y = xy
    patch = FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.02,rounding_size=0.02",
        linewidth=1.2,
        facecolor="white"
    )
    ax.add_patch(patch)
    ax.text(x + w/2, y + h/2, text, ha="center", va="center", fontsize=fontsize, wrap=True)

def arrow(ax, start, end):
    ax.add_patch(FancyArrowPatch(start, end, arrowstyle="->", mutation_scale=14, linewidth=1.2))

fig, ax = plt.subplots(figsize=(11, 6))
ax.set_axis_off()

# Layout coordinates (0..1 figure space)
# Sources
box(ax, (0.03, 0.72), 0.22, 0.20, "ERA5 hourly weather\n(t2m, RH, wind)", fontsize=10)
box(ax, (0.03, 0.45), 0.22, 0.20, "FIRMS / VIIRS detections\n(point events)", fontsize=10)
box(ax, (0.03, 0.18), 0.22, 0.20, "DEM raster\n(elevation)", fontsize=10)

# Processing steps
box(ax, (0.33, 0.72), 0.26, 0.20, "Aggregate to cell-day:\nTmax, RHmin, Wmax", fontsize=10)
box(ax, (0.33, 0.45), 0.26, 0.20, "Spatial join to grid:\nfire[t] per cell-day", fontsize=10)
box(ax, (0.33, 0.18), 0.26, 0.20, "Derive topo:\nelev, slope, aspect\n(northness/eastness)", fontsize=10)

# Fuel
box(ax, (0.33, 0.02), 0.26, 0.12, "Land cover → fuel fractions\n(sum to 1)", fontsize=10)

# Final table
box(ax, (0.70, 0.35), 0.27, 0.30, "Final modeling table\n(one row = cell_id × date)\nFeatures: weather + topo + fuels\nLabel: fire_tomorrow", fontsize=10)

# Arrows
arrow(ax, (0.25, 0.82), (0.33, 0.82))
arrow(ax, (0.25, 0.55), (0.33, 0.55))
arrow(ax, (0.25, 0.28), (0.33, 0.28))

arrow(ax, (0.59, 0.82), (0.70, 0.55))
arrow(ax, (0.59, 0.55), (0.70, 0.50))
arrow(ax, (0.59, 0.28), (0.70, 0.45))
arrow(ax, (0.59, 0.08), (0.70, 0.42))

ax.set_title("Preprocessing Pipeline: From Raw Sources to Cell-Day Dataset", fontsize=14, pad=10)
plt.tight_layout()
plt.savefig(OUT_PNG, dpi=300)
print("Saved:", OUT_PNG)
