# make_fig3_label_schematic.py
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

OUT_PNG = "thesis/figures/fig3_label_construction.png"

def box(ax, x, y, w, h, text, fontsize=10):
    patch = FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.02,rounding_size=0.02",
        linewidth=1.2,
        facecolor="white"
    )
    ax.add_patch(patch)
    ax.text(x + w/2, y + h/2, text, ha="center", va="center", fontsize=fontsize, wrap=True)

def arrow(ax, start, end, text=None):
    ax.add_patch(FancyArrowPatch(start, end, arrowstyle="->", mutation_scale=14, linewidth=1.2))
    if text:
        mx = (start[0] + end[0]) / 2
        my = (start[1] + end[1]) / 2
        ax.text(mx, my + 0.04, text, ha="center", va="bottom", fontsize=10)

fig, ax = plt.subplots(figsize=(11, 3.8))
ax.set_axis_off()

# Timeline baseline
ax.plot([0.05, 0.95], [0.30, 0.30], linewidth=1.2)

# Day markers
for x, label in [(0.15, "Day t"), (0.50, "Day t+1"), (0.85, "Day t+2")]:
    ax.plot([x, x], [0.26, 0.34], linewidth=1.2)
    ax.text(x, 0.20, label, ha="center", va="top", fontsize=11)

# Feature box at day t
box(ax, 0.07, 0.55, 0.28, 0.25,
    "Features at day t\n(weather summaries +\nstatic topo + fuels)", fontsize=10)

# Fire today at day t
box(ax, 0.07, 0.05, 0.28, 0.17,
    "fire[t]\n(observed, not used\nas predictor)", fontsize=10)

# Label fire tomorrow at t+1
box(ax, 0.39, 0.05, 0.28, 0.17,
    "fire_tomorrow[t]\n= fire[t+1]", fontsize=10)

# Prediction arrow from features to label
arrow(ax, (0.21, 0.55), (0.53, 0.22), text="Model predicts")

# Shift arrow fire[t] -> fire_tomorrow[t] via t+1
arrow(ax, (0.21, 0.13), (0.53, 0.13), text="shift within cell_id")

ax.set_title("Next-Day Label Construction (per grid cell)", fontsize=14, pad=8)
plt.tight_layout()
plt.savefig(OUT_PNG, dpi=300)
print("Saved:", OUT_PNG)
