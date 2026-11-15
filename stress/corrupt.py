"""Corrupt clean annotations the way a real model's output is messy.

Each corruption takes a loaded Photo, a random.Random and a strength, and
returns a new Photo. Used in memory by run_all.py; the CLI dumps one
corrupted copy of the dataset to disk so it can be looked at or fed to
`python -m assigner`:

    python stress/corrupt.py jitter 15 --out stress/samples/jitter_15
"""
import argparse
import glob
import json
import os
import random
import sys
from dataclasses import replace

from shapely.geometry import LineString

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from assigner.load import load_photo  # noqa: E402


def pieces_of(geom):
    return [g for g in getattr(geom, "geoms", [geom]) if not g.is_empty and g.area > 0]


def jitter(photo, rng, px):
    """Grow or shrink every outline by a random amount up to px. Model edges
    are never exact, and a damage that grows while its part shrinks spills
    onto the neighbour."""
    def j(s):
        g = s.geom.buffer(rng.uniform(-px, px))
        return None if g.is_empty else replace(s, geom=g)
    return replace(photo, damages=[x for x in map(j, photo.damages) if x],
                   parts=[x for x in map(j, photo.parts) if x])


def drop_parts(photo, rng, p):
    """Delete each part with probability p: the part model missed a panel."""
    return replace(photo, parts=[s for s in photo.parts if rng.random() >= p])


def swap_lr(photo, rng, p):
    """Flip left/right in a part name with probability p: the most common
    naming error upstream, and invisible to the assigner."""
    def sw(s):
        if rng.random() < p and ("left" in s.label or "right" in s.label):
            return replace(s, label=s.label.replace("left", "#").replace("right", "left").replace("#", "right"))
        return s
    return replace(photo, parts=[sw(s) for s in photo.parts])


def fragment(photo, rng, n):
    """Cut each damage into n pieces with a 4 px gap: a long scratch detected
    as several short ones."""
    out = []
    for s in photo.damages:
        minx, miny, maxx, maxy = s.geom.bounds
        pieces = [s.geom]
        for k in range(1, n):
            x = minx + (maxx - minx) * k / n + rng.uniform(-5, 5)
            cut = LineString([(x, miny - 1), (x, maxy + 1)]).buffer(2)
            pieces = [p for g in pieces for p in pieces_of(g.difference(cut))]
        out += [replace(s, id=f"{s.id}_{i + 1}", geom=g) for i, g in enumerate(pieces)]
    return replace(photo, damages=out)


CORRUPTIONS = {
    "jitter": (jitter, [5, 15, 30], "px"),
    "drop_parts": (drop_parts, [0.1, 0.3, 0.5], "p"),
    "swap_lr": (swap_lr, [0.1, 0.3, 0.5], "p"),
    "fragment": (fragment, [2, 3, 4], "pieces"),
}


def to_doc(photo):
    # back to the input format; masks come out as polygons, multi-part
    # geometries keep their largest piece
    def items(shapes, key):
        out = []
        for s in shapes:
            g = max(pieces_of(s.geom), key=lambda g: g.area)
            out.append({"id": s.id, key: s.label, "score": s.score,
                        "polygon": [[round(x), round(y)] for x, y in g.exterior.coords[:-1]]})
        return out
    return {"image_id": photo.image_id, "car_id": photo.car_id, "width": photo.width,
            "height": photo.height, "damages": items(photo.damages, "type"), "parts": items(photo.parts, "name")}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("corruption", choices=CORRUPTIONS)
    ap.add_argument("level", type=float)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--inputs", default="data/annotations/*.json")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    fn, _, unit = CORRUPTIONS[a.corruption]
    level = int(a.level) if unit != "p" else a.level
    rng = random.Random(a.seed)
    os.makedirs(a.out, exist_ok=True)
    for path in sorted(glob.glob(a.inputs)):
        doc = to_doc(fn(load_photo(path), rng, level))
        json.dump(doc, open(os.path.join(a.out, os.path.basename(path)), "w"), indent=1)
        print("wrote", os.path.join(a.out, os.path.basename(path)))
