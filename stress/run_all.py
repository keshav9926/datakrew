"""Run every corruption at every strength with several random seeds, score
each run against the expected reports and print the results table.

    python stress/run_all.py
"""
import glob
import json
import os
import random
import sys
from statistics import mean

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from assigner.assign import assign          # noqa: E402
from assigner.load import load_photo        # noqa: E402
from assigner.report import build_report    # noqa: E402
from stress.corrupt import CORRUPTIONS      # noqa: E402
from stress.score import pairs, score       # noqa: E402

SEEDS = 10
paths = sorted(glob.glob("data/annotations/*.json"))
expected = {}
for p in glob.glob("data/expected/*.json"):
    e = json.load(open(p))
    expected[e["image_id"]] = e


def run(photos):
    reports = {ph.image_id: build_report(ph, assign(ph)) for ph in photos}
    m = score(reports, expected)
    # diagnostic, not part of the score: how many wrong damage->part
    # assignments were nearest-part guesses
    m["wrong"] = m["guessed"] = 0
    for image_id, r in reports.items():
        right = pairs(expected[image_id])
        for d in r["damages"]:
            for h in d["parts"]:
                if (h["name"], d["type"]) not in right:
                    m["wrong"] += 1
                    m["guessed"] += "nearest_part_fallback" in d["flags"]
    return m


clean = run([load_photo(p) for p in paths])
assert clean["exact"] == 1.0, f"clean data should score perfectly, got {clean}"
rows = [("clean", "-", clean)]

for name, (corrupt, levels, unit) in CORRUPTIONS.items():
    for level in levels:
        runs = []
        for seed in range(SEEDS):
            rng = random.Random(seed)
            runs.append(run([corrupt(load_photo(p), rng, level) for p in paths]))
        rows.append((name, f"{level} {unit}", {k: mean(r[k] for r in runs) for k in runs[0]}))

print(f"mean over {SEEDS} seeds, {len(paths)} photos, "
      f"{sum(len(e['summary']) for e in expected.values())} expected (part, type) pairs\n")
print("| corruption | strength | precision | recall | F1 | photos exactly right | wrong answers that were fallback guesses |")
print("|---|---|---|---|---|---|---|")
for name, level, m in rows:
    guessed = f"{m['guessed'] / m['wrong'] * 100:.0f}%" if m["wrong"] else "-"
    print(f"| {name} | {level} | {m['precision']:.2f} | {m['recall']:.2f} | {m['f1']:.2f} "
          f"| {m['exact'] * 100:.0f}% | {guessed} |")
