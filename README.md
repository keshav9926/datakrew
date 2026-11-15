# Datakrew take-home: damage-to-part assigner

Takes one JSON file per photo (damage outlines + car part outlines, as produced
by upstream models) and writes a damage report saying which part each damage
is on, with a confidence. No models, no GPU.

## Run it

```
python -m venv .venv
.venv\Scripts\activate          # on Windows; source .venv/bin/activate elsewhere
pip install -r requirements.txt

python -m assigner examples/*.json --out report.json
python -m assigner data/annotations/*.json --out report.json
pytest
```

Globs are expanded by the program itself, so the same command works on Windows.

## Repo layout

| Path | What |
|---|---|
| `assigner/load.py` | read json, validate, polygon or RLE mask -> shapely geometry |
| `assigner/assign.py` | damage -> part(s) with confidence, hard-case rules |
| `assigner/report.py` | output schema |
| `assigner/__main__.py` | CLI |
| `tests/test_hard_cases.py` | hand-made tests for the three most important hard cases |
| `examples/` | the assignment's example photo (one polygon damage, one mask damage) |
| `data/` | 2b: photos, annotations, expected reports, unclear cases (TODO) |
| `stress/` | 2c: corruption script, scorer, results (TODO) |
| `docs/` | Part 1 memo, 2d vision answers (TODO) |
| `DECISION_LOG.md` | choices made and what I'd change with more time (TODO) |

## Input

Exactly the format in the assignment. Each damage/part carries `id`, `type`
(damage) or `name` (part), `score`, and either a `polygon` or an RLE `mask`.

### Invalid input policy

The rule is: never lose a whole photo because of one bad item. Every dropped
or repaired item leaves a line in the report's `warnings` so it is visible.

| Problem | What happens |
|---|---|
| top-level field missing (`image_id`, `width`, ...) | the file is skipped with an error on stderr, other files continue |
| polygon with < 3 points, or zero area | item dropped |
| self-intersecting polygon | repaired with `buffer(0)`, kept |
| mask whose counts don't sum to `height x width` | item dropped |
| outline partly outside the photo | clipped to the photo, kept |
| no `score` | assumed 1.0 |
| unknown damage type | kept, warned |

Both polygons and masks become shapely geometries in pixel coordinates. A mask
cell covers `(photo width / mask width) x (photo height / mask height)` pixels;
each horizontal run of 1-cells becomes one rectangle and the rectangles are
unioned.

## How assignment works

For each damage `d` and part `p`:

```
overlap(d, p) = area(d ∩ p) / area(d)        # fraction of the damage inside the part
confidence    = overlap x d.score x p.score
```

`d` is assigned to every part with `overlap >= 0.2`. Fraction-of-damage is used
instead of IoU because a small scratch fully inside a large bumper should
score 1.0, not something close to 0.

### Hard cases and the rule for each

| Case | Rule |
|---|---|
| damage spans two parts | assigned to both, each with its own overlap; flag `multi_part` |
| part outlines overlap each other (light drawn over the bumper edge) | the smaller part keeps the shared region, so overlaps sum to at most 1 |
| part inside another part (window inside door) | same rule: the smaller (inner) part wins |
| damage touches no part | nearest part if within 2% of the photo diagonal, flag `nearest_part_fallback`, confidence capped at what a barely-passing overlap would give; otherwise part `unknown`, flag `no_part` |
| sliver overlap on the neighbour from boundary noise | the 0.2 threshold ignores it |
| same damage detected twice | same type and IoU > 0.5 -> merged, higher score kept, warned |
| low-score detection (< 0.3) | kept, flag `low_score` |
| invalid / out-of-bounds outlines | see the policy table above |

### What it still cannot handle

- Left/right is taken from the part model's names as-is. If the part model
  says `front_left_door` for the right door, so does the report.
- Damage hidden behind reflections, dirt or occlusion: nothing to assign.
- Mask outlines are only accurate to one mask cell, so assignment within a
  cell's width of a part boundary is a coin flip.
- One dent seen in several photos of the same car is reported once per photo;
  cross-photo merging is out of scope here (see the vision answers).

## Output schema

One JSON list, one entry per photo:

```json
{
  "image_id": "car42_front",
  "car_id": "car42",
  "damages": [
    {
      "damage_id": "d1", "type": "scratch", "score": 0.81, "source": "polygon",
      "parts": [
        {"part_id": "p1", "name": "front_bumper",     "overlap": 0.68, "confidence": 0.523},
        {"part_id": "p2", "name": "front_left_light", "overlap": 0.32, "confidence": 0.233}
      ],
      "primary_part": "front_bumper",
      "flags": ["multi_part"]
    }
  ],
  "summary": [
    {"part": "front_bumper", "type": "scratch"},
    {"part": "front_left_light", "type": "scratch"}
  ],
  "warnings": []
}
```

- `parts` is sorted by overlap, `primary_part` is the first one.
- `summary` is the set of (part, damage type) pairs. This is what the stress
  test scores against the expected reports.
- `flags`: `multi_part`, `nearest_part_fallback`, `no_part`, `low_score`.
- `warnings`: anything dropped, repaired or merged while loading.

## Part names

snake_case, left and right are the **car's own** left and right as seen from
the driver's seat (so in a photo of the front of the car, the car's left is on
the viewer's right).

`front_bumper, rear_bumper, hood, trunk, roof, grille, windshield, rear_window,
front_left_door, front_right_door, rear_left_door, rear_right_door,
front_left_fender, front_right_fender, rear_left_quarter_panel,
rear_right_quarter_panel, front_left_light, front_right_light, rear_left_light,
rear_right_light, left_mirror, right_mirror, front_left_wheel,
front_right_wheel, rear_left_wheel, rear_right_wheel, front_left_window,
front_right_window, rear_left_window, rear_right_window, left_sill, right_sill,
number_plate`

Damage types are fixed by the assignment: `broken_glass, flat_tyre,
broken_lamp, dent, scratch, crack`.

## Why these three tests

1. **Damage spanning two parts**: the most common real case (scratches run
   along seams) and the one a naive "pick the best part" version gets wrong.
2. **Damage touching no part**: the part model missing a part is the most
   damaging upstream failure; the test pins down both the recovery (near) and
   the honest answer (far -> unknown).
3. **Sliver overlap + nested parts**: both are about boundary noise, which is
   what real masks look like; they check that the threshold and the
   smaller-part rule do what the README says.

Plus a cheap RLE round-trip test, because a wrong decoder would silently
shift every mask.

## Dataset, stress test, memo, vision answers, decision log

TODO: filled in as those parts are done.

## AI tools used

Claude Code (Anthropic) was used for planning the work, scaffolding the
package and tests, and reviewing the logic. Photo selection, annotation,
the expected reports and the decisions in the decision log are my own.
