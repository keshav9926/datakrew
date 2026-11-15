"""Score reports against expected reports with the Part 1 definition of
correct: a report is its set of (part, damage type) pairs.

    python stress/score.py report.json "data/expected/*.json"
"""
import glob
import json
import sys


def pairs(report):
    return {(s["part"], s["type"]) for s in report["summary"]}


def score(reports, expected):
    """reports, expected: dicts image_id -> report. Micro-averaged pair-level
    precision / recall / F1, plus the fraction of photos whose pair set is
    exactly right."""
    tp = fp = fn = exact = 0
    for image_id, exp_report in expected.items():
        got, exp = pairs(reports[image_id]), pairs(exp_report)
        tp += len(got & exp)
        fp += len(got - exp)
        fn += len(exp - got)
        exact += got == exp
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * p * r / (p + r) if p + r else 0.0
    return {"precision": p, "recall": r, "f1": f1, "exact": exact / len(expected)}


if __name__ == "__main__":
    reports = {r["image_id"]: r for r in json.load(open(sys.argv[1]))}
    expected = {}
    for path in glob.glob(sys.argv[2]):
        e = json.load(open(path))
        expected[e["image_id"]] = e
    for k, v in score(reports, expected).items():
        print(f"{k:10s} {v:.3f}")
