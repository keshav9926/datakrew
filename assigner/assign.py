"""Decide which part(s) each damage sits on."""
from dataclasses import replace

OVERLAP_THRESHOLD = 0.2   # fraction of the damage that must lie inside a part
NEAREST_MARGIN = 0.02     # fallback search radius, fraction of the photo diagonal
DUPLICATE_IOU = 0.5       # same type + this much overlap = the same damage twice
LOW_SCORE = 0.3


def carve_parts(parts):
    """Where part outlines overlap, the smaller part keeps the shared region:
    a window drawn inside a door stays a window, a light drawn over the
    bumper edge stays a light. Overlap fractions then sum to at most 1."""
    carved, taken = [], None
    for p in sorted(parts, key=lambda p: p.geom.area):
        g = p.geom if taken is None else p.geom.difference(taken)
        if not g.is_empty:
            carved.append(replace(p, geom=g))
        taken = p.geom if taken is None else taken.union(p.geom)
    return carved


def iou(a, b):
    inter = a.intersection(b).area
    return inter / (a.area + b.area - inter) if inter else 0.0


def merge_duplicates(damages, warnings):
    # same type and mostly the same pixels -> keep the higher-scoring one
    kept = []
    for d in sorted(damages, key=lambda d: -d.score):
        twin = next((k for k in kept if k.label == d.label and iou(k.geom, d.geom) > DUPLICATE_IOU), None)
        if twin:
            warnings.append(f"{d.id}: duplicate of {twin.id}, merged")
        else:
            kept.append(d)
    return kept


def hit(part, frac, damage, confidence=None):
    if confidence is None:
        confidence = frac * damage.score * part.score
    return {"part_id": part.id, "name": part.label,
            "overlap": round(frac, 3), "confidence": round(confidence, 3)}


def assign_one(damage, parts, diagonal):
    hits, flags = [], []
    for p in parts:
        frac = damage.geom.intersection(p.geom).area / damage.geom.area
        if frac >= OVERLAP_THRESHOLD:
            hits.append(hit(p, frac, damage))

    if not hits and parts:
        nearest = min(parts, key=lambda p: damage.geom.distance(p.geom))
        dist = damage.geom.distance(nearest.geom)
        margin = NEAREST_MARGIN * diagonal
        if dist <= margin:
            # a guess is never more confident than a barely-passing overlap
            conf = (1 - dist / margin) * OVERLAP_THRESHOLD * damage.score * nearest.score
            hits.append(hit(nearest, 0.0, damage, conf))
            flags.append("nearest_part_fallback")

    if not hits:
        hits.append({"part_id": None, "name": "unknown", "overlap": 0.0, "confidence": 0.0})
        flags.append("no_part")

    hits.sort(key=lambda h: -h["overlap"])
    if len(hits) > 1:
        flags.append("multi_part")
    if damage.score < LOW_SCORE:
        flags.append("low_score")
    return {"damage_id": damage.id, "type": damage.label, "score": damage.score,
            "source": damage.source, "parts": hits,
            "primary_part": hits[0]["name"], "flags": flags}


def assign(photo):
    diagonal = (photo.width ** 2 + photo.height ** 2) ** 0.5
    parts = carve_parts(photo.parts)
    damages = merge_duplicates(photo.damages, photo.warnings)
    return [assign_one(d, parts, diagonal) for d in damages]
