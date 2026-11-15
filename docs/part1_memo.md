# Part 1: Framing the problem

**Assumptions.** The customer is a motor insurer. After an incident,
policyholders take 4–8 phone photos of their car in a claims app. The system
helps an adjuster and never approves a payout on its own. Part names are a
fixed list of 33 (README).

## 1. Users and output

The main user is the **claims adjuster**. They use the report to **triage**
(settle a cosmetic claim from the desk, or send an assessor or a tow truck), to
**start the estimate** (repairers price per part, so the report is organised by
part) and to **check the story** (a "rear-end" claim with only front damage
gets a second look).

The report, per photo and then merged per car:

- **one line per damage**: type, part (the car's own left/right), confidence, and the photo and outline it came from, so the adjuster can check it in seconds;
- **a summary**: the set of (part, damage type) pairs, which become the estimate lines;
- **flags** for where to look: damage across two parts, part guessed from the nearest outline, no part found (`unknown`), low detector score.

No severity or cost: neither is reliable from one phone photo, and prices live
in the insurer's own tables, keyed by (part, type). A confident wrong part is
worse than `unknown`: the wrong part gets paid for, `unknown` gets a human look.

## 2. Definition of correct

**Ground truth.** For each photo an expert lists the visible (part, damage
type) pairs, following written rules so two experts agree:

- left/right is the car's own;
- a damage is listed on every part a repairer would have to work on (a key line across the door seam: both doors; a crease that only bends the fender: fender only);
- hidden damage is not listed; several scratches on one part are one pair;
- every unsure call is written down with the decision.

**One photo.** A predicted pair is correct only if the part and the type both
match an expected pair exactly. `unknown` is not a part: it is never a wrong
claim, but the pair it should have found counts as missed. A photo is
**right** when nothing is missed and no wrong part is claimed.

**Many photos.** Count correct, wrong and missed pairs over all photos;
report precision, recall, F1 and the share of photos that are right. Precision
and recall stay separate: a wrong pair pays for a repair nobody needs, a miss
costs a re-inspection or a dispute.

**Ignored on purpose:** confidence values, outline accuracy and damage counts.
Outline overlap (IoU) would punish a 10 px boundary disagreement that changes
nothing in the estimate, yet not notice a wrong side. Blind spot: one scratch
split into four detections scores the same as one.

## 3. Failure modes

Ranked by **how bad × how often**. "Bad" weighs plausible-looking errors above
ones an adjuster would spot in the photo.

| # | Failure on real photos | How often | Why it ranks here |
|---|---|---|---|
| 1 | Small or thin damage missed in far-away or dim photos | very often: whole-side shots at dusk | silent: the report looks complete |
| 2 | Part outline missing (dark, reflective or cropped panel) or left/right swapped | often | confidently wrong. Stress test: F1 0.71 with 30% of parts dropped, 0.80 with 30% of sides swapped |
| 3 | Reflections, dirt or shadows read as damage | often on glossy or wet cars | costs review time, but visible in the photo |
| 4 | Wrong damage type (scratch vs crack, smashed lamp vs broken glass) | sometimes | right part, wrong repair method and price |
| 5 | Same damage counted twice across photos of one car | every multi-photo claim | inflates the estimate; fixable when merging |
| 6 | Outline edges a few pixels off | always | no effect below ~30 px in the stress test |

## 4. Data

In priority order:

1. **An evaluation set first.** A few hundred real claim photos spread across distance, light, weather and paint, labelled by two annotators with the rules above; disagreements settled and logged. This set, not training metrics, decides what ships.
2. **Damage training data.** Start from CarDD (about 4,000 images, the same six types), but public photos skew towards close, well-lit shots, so add the insurer's past claim photos. Their final estimates list the parts repaired and the work done, a free rough label per claim. Outline by hand only where the model and the estimate disagree.
3. **Part training data.** Parts are rigid and on every car, so a few thousand SAM-assisted outlines go a long way. Keep wide shots: left/right needs the whole car in view.
4. **Hard cases on purpose:** night, rain, dirt, 3 m shots, plus close-ups darkened and shrunk.

Claim photos are shared under a data agreement, with plates and faces blurred
before labelling.
