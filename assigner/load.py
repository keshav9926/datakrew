"""Read one photo json and turn every outline (polygon or RLE mask) into a
shapely geometry in pixel coordinates. Bad items are dropped with a warning,
the rest of the photo is still processed."""
import json
from dataclasses import dataclass, field

import numpy as np
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

DAMAGE_TYPES = {"broken_glass", "flat_tyre", "broken_lamp", "dent", "scratch", "crack"}
REQUIRED = ("image_id", "car_id", "width", "height", "damages", "parts")


@dataclass
class Shape:
    id: str
    label: str      # damage type, or part name
    score: float
    geom: object    # shapely geometry, pixel coords
    source: str     # "polygon" or "mask"


@dataclass
class Photo:
    image_id: str
    car_id: str
    width: int
    height: int
    damages: list
    parts: list
    warnings: list = field(default_factory=list)


def decode_rle(counts, h, w):
    # row-major, runs alternate 0s / 1s and always start with 0s
    if sum(counts) != h * w:
        raise ValueError(f"counts sum to {sum(counts)}, grid is {h}x{w}={h * w}")
    flat = np.zeros(h * w, dtype=bool)
    pos, ones = 0, False
    for c in counts:
        if ones:
            flat[pos:pos + c] = True
        pos += c
        ones = not ones
    return flat.reshape(h, w)


def mask_to_geom(mask, img_w, img_h):
    # the mask is stretched over the whole photo, so one cell covers a
    # (img_w/w) x (img_h/h) block. One box per horizontal run of 1s, then union.
    h, w = mask.shape
    sx, sy = img_w / w, img_h / h
    boxes = []
    for r in range(h):
        row = mask[r]
        c = 0
        while c < w:
            if not row[c]:
                c += 1
                continue
            start = c
            while c < w and row[c]:
                c += 1
            boxes.append(box(start * sx, r * sy, c * sx, (r + 1) * sy))
    return unary_union(boxes) if boxes else None


def polygon_to_geom(points):
    if len(points) < 3:
        return None
    g = Polygon(points)
    if not g.is_valid:
        g = g.buffer(0)   # repairs bow-ties / self-touching rings in practice
    return None if g.is_empty or g.area == 0 else g


def load_shape(raw, label_key, photo):
    sid = str(raw.get("id", "?"))
    warn = photo.warnings
    label = raw.get(label_key)
    if not label:
        warn.append(f"{sid}: missing '{label_key}', dropped")
        return None
    score = raw.get("score")
    if score is None:
        warn.append(f"{sid}: no score, assuming 1.0")
        score = 1.0

    try:
        if "polygon" in raw:
            geom, source = polygon_to_geom(raw["polygon"]), "polygon"
        elif "mask" in raw:
            m = raw["mask"]
            grid = decode_rle(m["counts"], m["height"], m["width"])
            geom, source = mask_to_geom(grid, photo.width, photo.height), "mask"
        else:
            warn.append(f"{sid}: neither polygon nor mask, dropped")
            return None
    except (ValueError, TypeError, KeyError) as e:
        warn.append(f"{sid}: unreadable outline ({e}), dropped")
        return None

    if geom is None:
        warn.append(f"{sid}: empty or degenerate outline, dropped")
        return None

    frame = box(0, 0, photo.width, photo.height)
    if not frame.contains(geom):
        geom = geom.intersection(frame)
        warn.append(f"{sid}: outline went outside the photo, clipped")
        if geom.is_empty:
            return None
    return Shape(sid, label, float(score), geom, source)


def load_photo(path):
    with open(path) as f:
        raw = json.load(f)
    missing = [k for k in REQUIRED if k not in raw]
    if missing:
        raise ValueError(f"missing top-level fields {missing}")
    photo = Photo(raw["image_id"], raw["car_id"], int(raw["width"]), int(raw["height"]), [], [])
    for d in raw["damages"]:
        s = load_shape(d, "type", photo)
        if s:
            if s.label not in DAMAGE_TYPES:
                photo.warnings.append(f"{s.id}: unknown damage type '{s.label}', kept")
            photo.damages.append(s)
    for p in raw["parts"]:
        s = load_shape(p, "name", photo)
        if s:
            photo.parts.append(s)
    return photo
