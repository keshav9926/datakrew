def build_report(photo, assignments):
    # summary = the set of (part, damage type) pairs; that is what gets scored
    pairs = sorted({(h["name"], a["type"]) for a in assignments for h in a["parts"]})
    return {
        "image_id": photo.image_id,
        "car_id": photo.car_id,
        "damages": assignments,
        "summary": [{"part": p, "type": t} for p, t in pairs],
        "warnings": photo.warnings,
    }
