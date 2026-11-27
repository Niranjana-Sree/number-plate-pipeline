# Rules and settings from the company-server pipeline (CCPD run)

## Detection (LocateAnything-3B)
- Query: `car</c>truck</c>bus</c>motorcycle</c>bicycle</c>number plate`
- max_new_tokens 8192, temperature 0.7, top_p 0.9, rep. penalty 1.1, batch size 1
- Output boxes are 0-1000 normalised: pixel = value * W/1000 (x) and * H/1000 (y)
- Label containing "plate" = plate; everything else = vehicle

## make_csv_pilot.py rules (applied in this order; rows are flagged, never deleted)
1. Vehicle area < 10% of image -> `too_small`  (MIN_VEH_PCT = 10.0)
2. Vehicle duplicates: IoU >= 0.5, keep the larger -> `duplicate`  (IOU_THR = 0.5)
3. Plate WIDTH < 80 px (original image pixels) -> `far_plate`  (MIN_PLATE_W = 80)   [NOT 80%]
4. Plate duplicates: IoU >= 0.5, keep the larger -> `duplicate`
5. Plate centre must lie inside a kept vehicle box; matched to the smallest such vehicle, else `no_vehicle`

## final_select.py rules
- Candidates: plates with drop_reason "" or `no_vehicle`
- Plate matches a kept vehicle if centre-x is inside the vehicle's x-range AND vehicle y1 <= centre-y <= vehicle y2 + 0.40 * vehicle height (MARGIN = 0.40)
- Smallest-area matching vehicle wins; widest plate per image wins
- MAX_PAIRS = 1 pairs per image (raise for live frames with several vehicles)
- No match -> status `no_valid_pair`

## Plate crop and reading
- Crop = plate box + 10% margin each side, clamped to the image
- Enlarge crop 3x (LANCZOS) before Qwen
- Prompt: "Read the license plate in this image. Reply with only the plate characters, no spaces and no other text."
- do_sample=False, max_new_tokens=24; strip and remove spaces

## Baselines on CCPD (720x1160 close-ups)
- pilot200: 200/200 pairs correct; 9,000 imgs: 99.2% correct pair; 10,000 imgs: 99.69% plate recall at IoU 0.5, precision 97.98%
- Qwen 8B on 200 crops: 132 strict / 170 normalised / 193 last-6 chars

## Caveats
- 80 px, 10% and 40% were tuned on CCPD close-ups, not campus camera frames; re-tune on your frames
- Scripts key on `image_file`: every frame needs a UNIQUE filename (use chunk+frame in the name)
- make_csv_pilot.py label scoring needs CCPD labels; without them is_label_plate columns are blank and final_select prints "NOT the labeled one" - ignore that line
- run_some.py is REBUILT from description (original text not in chat); the other three are verbatim from chat
- At college "number plate" wording underperformed; "vehicle registration plate" worked on car1/car7 crops
