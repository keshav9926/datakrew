# Stress test (2c)

The hand-drawn outlines in `data/annotations/` are cleaner than any model's
output. `corrupt.py` damages them the way a real model would, `run_all.py`
reruns the assigner on every corrupted copy, and `score.py` scores the reports
against `data/expected/` using the Part 1 definition of correct.

```
python stress/run_all.py                                   # prints the table below, ~4 s
python stress/corrupt.py swap_lr 0.3 --out stress/samples/swap_lr   # write one corrupted copy to look at
python -m assigner "stress/samples/swap_lr/*.json" --out r.json
python stress/score.py r.json "data/expected/*.json"
```

## Corruptions and why

| corruption | what it does | why a real model does this | strengths |
|---|---|---|---|
| `jitter` | grows or shrinks every outline by a random amount, up to N px | segmentation edges are never exact, and blobby masks bleed over panel seams | 5, 15, 30 px |
| `drop_parts` | deletes each part outline with probability p | part models miss panels that are dark, reflective, dirty or half out of frame | 0.1, 0.3, 0.5 |
| `swap_lr` | swaps left and right in a part's name with probability p | left/right has to be inferred from the viewpoint, which is the classic part-model mistake on close-ups | 0.1, 0.3, 0.5 |
| `fragment` | cuts each damage into n pieces with a 4 px gap | long thin scratches and cracks come out as several short detections | 2, 3, 4 pieces |

The brief asks for three. I kept a fourth (fragmentation) because its result
shows a blind spot in the scoring rule (see below).

## Scoring

A report is its set of (part, damage type) pairs. A predicted pair is right
only if both the part name and the damage type match an expected pair.
`unknown` is not a part: it never counts as a wrong claim, but the expected
pair it should have found still counts as missed. So an honest "I don't know"
costs recall only, while a wrong guess costs precision and recall.
Precision, recall and F1 are pooled over all 12 expected pairs from the
5 photos. "Exactly right" is the share of photos with nothing missed and no
wrong part claimed. Each row is the mean over 10 random seeds.

The first run also counted `unknown` as a wrong claim. That scored an honest
"I don't know" the same as a confident wrong guess, so it was changed. Only
the `drop_parts` rows moved: F1 at p = 0.3 / 0.5 went from 0.70 / 0.52 to
0.71 / 0.57.

The last column is a diagnostic, not part of the score. It is the share of
wrong part claims that came from the nearest-part fallback, i.e. cases where
no part held 20% of the damage, so the assigner guessed the closest part.

## Results

| corruption | strength | precision | recall | F1 | photos exactly right | wrong answers that were fallback guesses |
|---|---|---|---|---|---|---|
| clean | - | 1.00 | 1.00 | 1.00 | 100% | - |
| jitter | 5 px | 1.00 | 1.00 | 1.00 | 100% | - |
| jitter | 15 px | 1.00 | 0.99 | 1.00 | 98% | - |
| jitter | 30 px | 0.95 | 0.97 | 0.96 | 80% | 0% |
| drop_parts | 0.1 p | 0.94 | 0.91 | 0.92 | 78% | 100% |
| drop_parts | 0.3 p | 0.75 | 0.68 | 0.71 | 46% | 100% |
| drop_parts | 0.5 p | 0.65 | 0.51 | 0.57 | 30% | 100% |
| swap_lr | 0.1 p | 0.93 | 0.93 | 0.93 | 82% | 0% |
| swap_lr | 0.3 p | 0.80 | 0.80 | 0.80 | 52% | 0% |
| swap_lr | 0.5 p | 0.68 | 0.68 | 0.68 | 32% | 0% |
| fragment | 2 pieces | 1.00 | 1.00 | 1.00 | 100% | - |
| fragment | 3 pieces | 1.00 | 1.00 | 1.00 | 100% | - |
| fragment | 4 pieces | 1.00 | 1.00 | 1.00 | 100% | - |

## Conclusions

Missing part outlines hurt the report most. At a 30% drop rate F1 falls to
0.71 and fewer than half the photos come out exactly right. Every wrong part
claim in those runs came from the nearest-part fallback guessing a neighbour
(a broken lamp reported on the bumper, a dent on the wheel), so an upstream
miss turns into a plausible-looking wrong answer instead of an honest
`unknown`.

Left/right swaps come next, and the assigner cannot see them at all because it
takes part names as given. Every swapped part that carries damage turns one
right pair into one wrong one.

Boundary noise barely matters until edges are about 30 px off. Fragmentation
did not move the score, but that is a blind spot of the pair-level metric, not
robustness: a scratch split into four is still listed four times in the
per-damage section.

**Fix first:** part recall upstream, because nothing downstream can recover a
panel that was never outlined. In the assigner, the fallback should only pick
parts that can carry that damage type (`broken_lamp` on lights, `flat_tyre` on
wheels, `broken_glass` on glass) and answer `unknown` otherwise.

## Limits of this test

- 12 expected pairs means each pair is about 8% of recall, so differences under
  about 0.05 are noise.
- Corruptions are applied one at a time. Real model output has all of them at
  once, so these numbers are optimistic.
- Corrupted damages keep their original types, so damage-type confusion
  (scratch vs crack) is not tested here.
