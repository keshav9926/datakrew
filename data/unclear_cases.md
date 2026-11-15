# Unclear cases while annotating

One bullet per doubt: what was unclear, what I decided, why.

## Which side is which

- **All photos**: left/right is the car's own, from the driver's seat. In car01 and car03 the grille is to the *right* of the headlight in the picture, so the camera is at the car's **right**-front corner (`front_right_light`, `front_right_fender`). In car02 the car's nose points right, so we are standing on the car's **left** (`front_left_door`, `rear_left_door`). In car05 the nose points left, so it is the **right** side (`front_right_wheel`). In car04 (head-on) the smashed side window is on the picture's right, which is the car's **left**.

## Damage type

- **car01 d4, headlight**: the lamp is knocked out of its mounts but the lens is intact. `broken_lamp` or no damage? Decided `broken_lamp`: a repairer would replace or refit the assembly, so the report must mention it. An insurer who only pays for broken lenses would disagree.
- **car03 d1, headlight**: lens shattered. `broken_lamp` or `broken_glass`? Decided `broken_lamp`: the part is a lamp; `broken_glass` is kept for windows and windscreens.
- **car03 d3, bumper**: the cover is torn open and a piece is missing. There is no "missing" or "detached" type; `crack` is the nearest. Outlined the torn edge only, not the hole.
- **car04 d1, windscreen**: shattered and crazed over the whole area, no single crack line. Decided `broken_glass`, not `crack`. A single star-crack would have been `crack` on `windshield`.
- **car02, faint lines**: under flash, some lines could be reflections. Outlined the three that are clearly continuous; ignored the fainter marks on the sill.

## Which part

- **car01 d3**: the gap at the fender / headlight / bumper junction. Dent on the fender, or just the bumper out of alignment? Decided `front_right_fender` dent: the fender edge itself is bent, the bumper is only displaced.
- **car03 d2**: the crease sits where the fender meets the hood seam. Decided fender only in the expected report; the outline does touch the hood, so the assigner may add `hood` with a small overlap. That is deliberate: it tests the overlap threshold on a real seam.
- **car02 d1**: one continuous key line crossing the door seam. One outline or two? Decided one outline, so the expected report has `scratch` on both doors. The report counts parts, not outlines, so it makes no difference to scoring, but it is the realistic model output.
- **car05 d1**: outline the tyre only or the whole wheel? Decided the whole tyre+rim as one shape, since "flat tyre" is a property of the wheel and the only sensible part is `front_right_wheel`.

## What was deliberately not outlined

- **car01**: areas under black tape near the wheel arch. Damage is hidden, so no outline; the expected report does not list it either.
- **car03**: the hole in the bumper showing the inner structure; debris and dirt inside it.
- **car04**: glass fragments on the hood (debris, not damage). Body parts not touching a damage (bumper, grille, lights) were still outlined as context, because a real part model would output them and the assigner must not be confused by them.
- **car02**: the rear quarter panel and the wheel are outlined as neighbours only; they carry no damage.

## Outlines corrected after the first assigner run

The expected reports were written before the first run and were not changed.
On the first run, two photos picked up an extra part at 21% overlap. Each
overlay was zoomed in on and only outlines that were visibly wrong were fixed:

- **car02 p7 rear_left_wheel**: ran ~35 px past the white wheel-arch lip onto the door. Redrawn to follow the lip.
- **car02 d3 scratch**: started on the arch lip, ~50 px before the scratch is actually visible. Start moved to where the line begins.
- **car04 d2 broken_glass and p4 front_left_window**: reached ~20 px down over the mirror housing. Bottom edge moved up to the window sill.

Risk: changing ground truth after seeing the output can quietly tune the data
to the code. That is why the expected reports stayed fixed and the
before/after is listed here.

## Outline precision

- Outlines were placed by reading pixel coordinates off a 50 px grid over each photo and checked on `data/preview/*.png`. They are good to roughly 10 px, which is coarser than a careful click-by-click tracing but finer than a 160x160 mask cell (6 x 4 px here). Two blob-shaped damages (car03 d2, car04 d1) are stored as RLE masks to exercise that code path on real photos.
