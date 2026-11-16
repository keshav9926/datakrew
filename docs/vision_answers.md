# 2d. Vision questions

## 1. Trained on close-ups, used on far-away photos in poor light

At 3 metres a scratch that filled the frame in training is now a few pixels
wide, and in poor light it has less contrast and more noise. So I expect:

- many more misses, mostly small damage (scratches, cracks, small dents);
- lower confidence on what it does find;
- more false alarms from shadows, reflections and noise it never saw up close;
- big obvious damage (smashed glass, flat tyre) still mostly fine.

Cheap check, no new labelling: take the close-up test set, shrink each photo
to what 3 m would look like, darken it and add noise, then rerun and compare
recall per class with the original. Then label about 50 real customer photos
and see if the drop matches. In production, watch detections per photo and
average confidence: a drop on far-away photos is the same problem showing up.

## 2. Six photos, one dent seen twice

Merge per part, not per photo. Each photo already gives (part, type) pairs
with the car's own left/right, so the dent on `front_left_door` seen in photos
2 and 3 becomes one car-level entry: keep the highest confidence and link both
photos so the adjuster can check.

To count separate dents on one part, I would also store where the damage sits
inside the part (front/back half, upper/lower half of the door) and merge only
when the position and type match.

Where it breaks:

- two real dents on the same door, close together, get merged into one;
- if one photo gets left/right wrong, the same dent ends up on two doors;
- at steep angles the position inside the part is distorted, so the same dent
  can look like two;
- a dent across two panels can be assigned differently in each photo.

## 3. Is mask IoU good for a long, thin scratch?

No. A scratch might be 300 px long but only 4 px wide. If the model draws it
in the right place but 3 px to the side, a human would call that correct, yet
the overlap is tiny and IoU is close to 0. Two annotators also disagree on the
width by a few pixels, so IoU mostly measures width noise, not whether the
scratch was found.

What matters for a scratch is its length and path. I would compare centre
lines with a tolerance:

```python
pred_line, true_line = skeleton(pred_mask), skeleton(true_mask)   # 1 px wide lines
precision = pred_line.intersection(true_line.buffer(5)).length / pred_line.length
recall    = true_line.intersection(pred_line.buffer(5)).length / true_line.length
```

That gives "how much of the drawn scratch is real" and "how much of the real
scratch was found", and a few pixels of sideways error no longer matter.

## 4. What does the table say, and what next?

Conclusions:

- Scratch and crack drop from 0.85 / 0.80 on training to 0.47 / 0.29 on test,
  so the model overfits on those classes or their labels are inconsistent.
- Small objects are bad for every class (0.05 to 0.18 for scratch, crack and
  dent), so size is the main problem, not one class.
- Crack has only 120 test examples, so its number is noisy too.

What I'd try, in order:

1. Look at 50 failures. Thin damage is often labelled inconsistently (where
   does a scratch end?). Cheapest step, may explain a lot.
2. Check the metric. Mask IoU at 0.5 is very harsh on thin shapes (see
   question 3), so part of the drop may be the score, not the model.
3. Higher input resolution or tiling, so small damage gets more pixels.
4. More scratch and crack data plus stronger augmentation for the overfitting.
