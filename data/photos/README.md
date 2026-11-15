# Photos

Five photos of damaged cars from Wikimedia Commons, chosen to cover all six
damage types and four viewpoints. Saved at 960 px width. The file stem is the
`image_id`; the part before the first underscore is the `car_id`.

| File | Source (Wikimedia Commons) | Author | Licence | What is in it |
|---|---|---|---|---|
| car01_front_right.jpg | [Oh deer!.jpg](https://commons.wikimedia.org/wiki/File:Oh_deer!.jpg) | Nyttend | Public domain | front-right corner hit: bumper dent + tear, fender edge bent, headlight knocked loose |
| car02_left_side.jpg | [KeyedPaintOnCar.JPG](https://commons.wikimedia.org/wiki/File:KeyedPaintOnCar.JPG) | Athol Mullen | CC BY-SA 4.0 | key scratches running across both left doors |
| car03_front_right.jpg | [Damaged car parked on gravel with broken front end and dirty headlight.jpg](https://commons.wikimedia.org/wiki/File:Damaged_car_parked_on_gravel_with_broken_front_end_and_dirty_headlight.jpg) | Shixart1985 | CC BY 2.0 | shattered headlight, creased fender, bumper torn open |
| car04_front.jpg | [SmashedWindowCar.JPG](https://commons.wikimedia.org/wiki/File:SmashedWindowCar.JPG) | Simon Speed | CC0 | windscreen and driver's window smashed |
| car05_right_side.jpg | [Flat Tire.JPG](https://commons.wikimedia.org/wiki/File:Flat_Tire.JPG) | Gerlach | Public domain | flat front-right tyre |

Outlines live in `../raw/labels_coco.json` (COCO polygon format) and are
converted to the assignment's input format with `scripts/convert_annotations.py`.
`../preview/` has the outlines drawn over each photo.
