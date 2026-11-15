"""Make Sense export -> assignment input json, one file per photo.

    python scripts/convert_annotations.py data/raw/labels_coco.json
    python scripts/convert_annotations.py data/raw/labels_coco.json --mask car02_front:d1

Accepts Make Sense's "single file in COCO json" export or its VGG json export.
A label is a damage if it is one of the six damage types, otherwise a part.
Ground truth gets score 1.0. --mask stores that damage as a 160x160 RLE mask
instead of a polygon so the mask code path is exercised on real data.
"""
import argparse
import json
import os
import sys

import numpy as np
import shapely
from PIL import Image
from shapely.geometry import Polygon

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from assigner.load import DAMAGE_TYPES  # noqa: E402

PHOTOS = "data/photos"
OUT = "data/annotations"
MASK_SIZE = 160


def encode_rle(grid):
    flat = grid.ravel().astype(np.int8)
    change = np.flatnonzero(np.diff(flat)) + 1
    counts = np.diff(np.concatenate([[0], change, [flat.size]])).tolist()
    return counts if flat[0] == 0 else [0] + counts   # runs must start with 0s


def polygon_to_mask(points, w, h):
    # a cell is 1 if its centre is inside the polygon
    poly = Polygon(points).buffer(0)
    cx = (np.arange(MASK_SIZE) + 0.5) * w / MASK_SIZE
    cy = (np.arange(MASK_SIZE) + 0.5) * h / MASK_SIZE
    X, Y = np.meshgrid(cx, cy)
    grid = shapely.contains_xy(poly, X.ravel(), Y.ravel()).reshape(MASK_SIZE, MASK_SIZE)
    return {"height": MASK_SIZE, "width": MASK_SIZE, "counts": encode_rle(grid)}


def read_export(path):
    """-> {filename: [(label, [[x, y], ...]), ...]}"""
    raw = json.load(open(path))
    out = {}
    if "annotations" in raw:                       # COCO
        names = {c["id"]: c["name"] for c in raw["categories"]}
        files = {i["id"]: i["file_name"] for i in raw["images"]}
        for a in raw["annotations"]:
            seg = a["segmentation"][0]
            pts = [[seg[i], seg[i + 1]] for i in range(0, len(seg), 2)]
            out.setdefault(files[a["image_id"]], []).append((names[a["category_id"]], pts))
    else:                                          # VGG
        for entry in raw.values():
            for r in entry["regions"]:
                sa = r["shape_attributes"]
                pts = [[x, y] for x, y in zip(sa["all_points_x"], sa["all_points_y"])]
                label = next(iter(r["region_attributes"].values()))
                out.setdefault(entry["filename"], []).append((label, pts))
    return out


def convert(filename, regions, masks):
    image_id = os.path.splitext(filename)[0]
    w, h = Image.open(os.path.join(PHOTOS, filename)).size
    doc = {"image_id": image_id, "car_id": image_id.split("_")[0],
           "width": w, "height": h, "damages": [], "parts": []}
    for label, pts in regions:
        if label in DAMAGE_TYPES:
            did = f"d{len(doc['damages']) + 1}"
            item = {"id": did, "type": label, "score": 1.0}
            if f"{image_id}:{did}" in masks:
                item["mask"] = polygon_to_mask(pts, w, h)
            else:
                item["polygon"] = pts
            doc["damages"].append(item)
        else:
            doc["parts"].append({"id": f"p{len(doc['parts']) + 1}", "name": label,
                                 "score": 1.0, "polygon": pts})
    return doc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("export", help="Make Sense COCO or VGG json")
    ap.add_argument("--mask", action="append", default=[], metavar="IMAGE_ID:DAMAGE_ID",
                    help="store this damage as an RLE mask (repeatable)")
    args = ap.parse_args()

    os.makedirs(OUT, exist_ok=True)
    for filename, regions in read_export(args.export).items():
        doc = convert(filename, regions, set(args.mask))
        path = os.path.join(OUT, doc["image_id"] + ".json")
        json.dump(doc, open(path, "w"), indent=1)
        kinds = ", ".join(f"{d['id']}={d['type']}" + ("(mask)" if "mask" in d else "") for d in doc["damages"])
        print(f"{path}: {len(doc['damages'])} damages [{kinds}], {len(doc['parts'])} parts")


if __name__ == "__main__":
    main()
