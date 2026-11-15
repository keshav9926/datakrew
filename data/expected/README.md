# Expected reports

One file per photo, written by looking at the photo (not by running the
assigner). `summary` is the list of (part, damage type) pairs a human expert
would give; it is scored against the `summary` in the assigner's output.

```json
{
  "image_id": "car01_front",
  "summary": [
    {"part": "front_bumper", "type": "scratch"},
    {"part": "front_left_light", "type": "broken_lamp"}
  ],
  "notes": "one line on anything that was not obvious"
}
```

Files: `car01_front.json` ... `car05_<view>.json`.
