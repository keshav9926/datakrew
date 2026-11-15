"""Draw the outlines from data/annotations/*.json over the photos, to eyeball
labels and left/right before trusting them.

    python scripts/preview.py data/annotations/car01_front.json   (opens a window)
    python scripts/preview.py data/annotations/*.json --save      (writes data/preview/*.png)
"""
import argparse
import glob
import json
import os
import sys

import matplotlib
import matplotlib.pyplot as plt
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from assigner.load import load_photo  # noqa: E402


def draw(path, save):
    photo = load_photo(path)
    raw = json.load(open(path))
    img = None
    for ext in (".jpg", ".jpeg", ".png"):
        p = os.path.join("data/photos", raw["image_id"] + ext)
        if os.path.exists(p):
            img = Image.open(p)
    fig, ax = plt.subplots(figsize=(10, 7))
    if img is not None:
        ax.imshow(img)
    for s, colour in [(p, "cyan") for p in photo.parts] + [(d, "red") for d in photo.damages]:
        geoms = getattr(s.geom, "geoms", [s.geom])
        for g in geoms:
            x, y = g.exterior.xy
            ax.plot(x, y, color=colour, linewidth=1.5)
        c = s.geom.centroid
        ax.text(c.x, c.y, f"{s.id} {s.label}", color=colour, fontsize=8,
                bbox=dict(facecolor="black", alpha=0.5, pad=1))
    ax.set_title(f"{raw['image_id']}  (cyan = parts, red = damages)")
    ax.set_xlim(0, photo.width)
    ax.set_ylim(photo.height, 0)
    if save:
        os.makedirs("data/preview", exist_ok=True)
        fig.savefig(os.path.join("data/preview", raw["image_id"] + ".png"), dpi=100, bbox_inches="tight")
        plt.close(fig)
    else:
        plt.show()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("inputs", nargs="+")
    ap.add_argument("--save", action="store_true")
    args = ap.parse_args()
    if args.save:
        matplotlib.use("Agg")
    for pattern in args.inputs:
        for path in sorted(glob.glob(pattern)):
            draw(path, args.save)
