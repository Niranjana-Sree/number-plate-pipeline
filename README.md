# Number-plate pipeline for recorded road-camera video

Turns recorded camera video into a per-vehicle CSV: vehicle box, plate box and plate text.
Built as a pilot on a college camera feed. It runs as **batch processing on recorded chunks**, not in real time.

## What it does
Video chunk -> frames (5 fps) -> LocateAnything-3B finds vehicles and plates -> near-lane filter ->
plate/vehicle pairing -> crop search for missed plates -> tracking (one row per vehicle, best crop) ->
Qwen3-VL-4B reads the plate -> state-code fix and Indian plate format check -> CSV.

| Stage | Script |
|---|---|
| frames, status tracking, batch loop | `pipeline.py`, `watch.py` |
| detections, lane filter, pairing | `scripts/make_csv_pilot.py`, `apply_roi.py`, `final_select.py` |
| crop search for missed plates | `scripts/second_pass_prep.py`, `shrink_crops.py`, `locate_crops_grouped.py`, `second_pass_merge.py` |
| tracking | `scripts/track_best.py` |
| plate reading and checks | `scripts/read_plates_d.py`, `fix_state.py`, `validate_plates.py`, `join_results.py` |
| evaluation | `eval/` |

## Pilot results
Hand-labelled by the author: 74 vehicles from 11 chunks (about 5.5 minutes, one camera, one afternoon).

| Metric | Result |
|---|---|
| Vehicle detection precision | 100% (74/74) |
| Plate visibility (human) | full 30%, partial 15%, not readable 55% |
| Exact plate match, fully visible plates | 50%, 68% with the state-code fix |
| Character accuracy, fully visible plates | 90% |
| End to end (correct plate / all real vehicles) | 15%, 20% with the state-code fix |

A prompt that lets the model answer `UNREADABLE` rejected 8 of 8 unreadable plates on 15 fresh vehicles (the earlier prompt: 0 of 8).
Fresh-chunk results: `<add after the batch run>`

## Limits (please read)
- Image blur is the main limit: 55% of plates are not readable in the image, so reader improvements cap end to end near 45%.
- Recall (vehicles the pipeline missed) is not measured; a hand count on 3 chunks varied from 2/10 to 7/9.
- Labels come from one person, on one camera and a short time window. The state-code fix was designed on the same 74 vehicles, so its numbers are optimistic.
- Batch only: about 7-9 minutes per 30-second chunk on an RTX PRO 2000 (16 GB).
- Qwen can produce plausible but wrong text on blurry plates. The format check flags impossible strings only.

## Setup
Tested on Windows 11, Python 3.12, NVIDIA GPU with CUDA 12.8.
1. `pip install -r requirements.txt`
2. Install ffmpeg and put it on PATH.
3. Download the models into `models/`:
   - `models/LocateAnything-3B` (must contain `batch_infer.py`): <source link>
   - `models/Qwen3-VL-4B-Instruct`: https://huggingface.co/Qwen/Qwen3-VL-4B-Instruct

## Run
1. Put video chunks in `chunks/` named `cam_YYYYMMDD_HHMMSS.mkv`.
2. `python watch.py --once --limit 1` processes one chunk (`--limit 10` for ten, no limit for all).
3. Outputs: `work/<chunk>/result.csv`, `all_results.csv`, `chunk_status.csv`.
   A sample with masked plate text is in `samples/all_results_sample.csv`.
4. Near-lane filter: `roi.json` holds the lane polygon for the original camera view.
   Draw a new one with `scripts/click_roi.py` if your camera view differs.

## Evaluate
`python eval/eval_tool.py` (label vehicles by hand), then `python eval/score_eval.py` and `python eval/score_fixed.py`.

## Repo layout
`scripts/` pipeline stages | `eval/` labelling and scoring | `experiments/` prompt comparisons |
`tools/` helper scripts (including a recorder that was used to collect the video) | `docs/` rules and settings | `samples/` masked sample output

## Credits
LocateAnything-3B and Qwen3-VL-4B-Instruct are third-party pretrained models used without fine-tuning.