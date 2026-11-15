# Decision log

Choices made while building this, and what I'd change with more time.

1. **Shapely polygons as the one internal shape.** A mask becomes a union of
   one rectangle per run of 1-cells, so polygons and masks share the same
   overlap and distance code, and a mask stays exact to its cells.
   *With more time:* nothing at this size; with thousands of large masks,
   rasterising everything to one grid would be faster.

2. **Overlap = share of the damage inside the part, assigned at ≥ 0.2.** IoU
   would give a small scratch on a big bumper a tiny score. The threshold sits
   close to the noise of hand-drawn outlines: the two extra parts in the first
   run held 21%. *With more time:* set it on a real evaluation set instead of
   by judgement.

3. **Confidence = overlap × damage score × part score.** Easy to explain and
   to check by hand, but not calibrated: 0.6 does not mean right 60% of the
   time. *With more time:* calibrate it on the evaluation set so adjusters can
   pick a review cut-off.

4. **Nearest-part fallback within 2% of the photo diagonal, else `unknown`.**
   It rescues damage sitting just outside a sloppy part outline. The stress
   test showed the cost: when part outlines go missing, every wrong part claim
   comes from this guess. *First change with more time:* only fall back to
   parts that can carry the damage type (lights for `broken_lamp`, wheels for
   `flat_tyre`, glass for `broken_glass`), else answer `unknown`.

5. **Hard-case rules kept simple.** The smaller of two overlapping parts keeps
   the shared area (window inside door, lamp over bumper edge); same-type
   damages with IoU > 0.5 are merged; scores under 0.3 are flagged, not
   dropped; one bad item never drops the photo, and every repair or drop is
   written to `warnings`. *With more time:* check left/right part names against
   the viewpoint; today they are taken on trust.

6. **"Correct" = the photo's set of (part, damage type) pairs.** That is what an
   adjuster turns into estimate lines, and two people score it the same way.
   `unknown` first counted as a wrong claim too; it now counts only as a miss,
   so an honest answer scores better than a wrong guess (F1 with 30% / 50% of
   parts dropped: 0.70 / 0.52 before, 0.71 / 0.57 after). *With more time:*
   score per car after merging photos, and count damages so a split scratch
   shows up.

7. **Commons photos, outlines placed from coordinate grids.** Licensed photos
   can live in the repo, and the converter also reads Make Sense exports, so
   anyone can redo the outlines by hand. Four outlines were fixed after the
   first run and logged; the expected reports were not touched.
   *With more time:* redo the outlines in CVAT with SAM, add a second
   annotator to measure agreement, and grow past 12 expected pairs (each one
   is about 8% of recall).

8. **Four corruptions, not three.** Fragmentation stayed because its perfect
   score exposes a blind spot in the metric, not robustness. Each corruption
   runs alone. *With more time:* combine them, and simulate what the memo
   ranks high but the stress test skips: false damage from reflections and
   damage-type confusion.
