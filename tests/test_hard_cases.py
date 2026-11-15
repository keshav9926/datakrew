import numpy as np
from shapely.geometry import box

from assigner.assign import assign
from assigner.load import Photo, Shape, decode_rle, mask_to_geom


def shape(sid, label, geom, score=1.0):
    return Shape(sid, label, score, geom, "polygon")


def photo(damages, parts, w=100, h=100):
    return Photo("t", "t", w, h, damages, parts)


# 1. a scratch lying across two adjacent panels must be reported on both
def test_damage_spanning_two_parts():
    door = shape("p1", "front_left_door", box(0, 0, 50, 50))
    fender = shape("p2", "front_left_fender", box(50, 0, 100, 50))
    scratch = shape("d1", "scratch", box(40, 20, 60, 22))
    [a] = assign(photo([scratch], [door, fender]))
    assert {h["name"]: h["overlap"] for h in a["parts"]} == {"front_left_door": 0.5, "front_left_fender": 0.5}
    assert "multi_part" in a["flags"]


# 2. damage touching no part: a near one is guessed and flagged, a far one is unknown
def test_no_part_fallback_and_unknown():
    bumper = shape("p1", "front_bumper", box(0, 0, 50, 50))
    near = shape("d1", "dent", box(51, 10, 55, 14))    # 1 px gap; diag 141 -> margin 2.8 px
    far = shape("d2", "dent", box(90, 90, 95, 95))
    a, b = assign(photo([near, far], [bumper]))
    assert a["primary_part"] == "front_bumper" and "nearest_part_fallback" in a["flags"]
    assert a["parts"][0]["confidence"] < 0.2
    assert b["primary_part"] == "unknown" and "no_part" in b["flags"]


# 3. a sliver of overlap is ignored, and a part drawn inside another part wins
def test_sliver_and_nested_parts():
    door = shape("p1", "front_left_door", box(0, 0, 100, 100))
    window = shape("p2", "front_left_window", box(20, 20, 60, 60))
    hood = shape("p3", "hood", box(100, 0, 200, 100))
    crack = shape("d1", "crack", box(30, 30, 50, 50))        # fully inside the window
    scratch = shape("d2", "scratch", box(70, 10, 102, 12))   # 2 of 32 px spill onto the hood
    a, b = assign(photo([crack, scratch], [door, window, hood], w=200))
    assert [h["name"] for h in a["parts"]] == ["front_left_window"]
    assert [h["name"] for h in b["parts"]] == ["front_left_door"]


def test_rle_round_trip():
    m = np.zeros((4, 5), dtype=bool)
    m[1, 1:3] = True
    m[2, 4] = True
    assert (decode_rle([6, 2, 6, 1, 5], 4, 5) == m).all()
    assert mask_to_geom(m, 50, 40).area == 3 * 10 * 10   # 10x10 px cells
