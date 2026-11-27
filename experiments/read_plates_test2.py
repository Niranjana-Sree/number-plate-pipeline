# repo root: the folder that contains scripts/, eval/ and models/
import os as _os
ROOT = _os.path.abspath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), ".."))
import os, sys, csv, glob, torch
from PIL import Image
from transformers import AutoProcessor, Qwen3VLForConditionalGeneration

M = _os.path.join(ROOT, 'models', 'Qwen3-VL-4B-Instruct')
CROPS = sys.argv[1]
OUT = sys.argv[2]
P_FMT = ("This is an Indian vehicle registration plate. Its format is: 2 letters for the state (for example TN), "
         "2 digits, 1 to 3 letters, then 4 digits. Read the plate. Reply with only the plate characters, no spaces and no other text.")
P_D = ("This is a photo of an Indian vehicle registration plate. If the plate is blurry, cut off, or you cannot clearly read "
       "every character, reply exactly: UNREADABLE. Never guess or invent characters. Otherwise reply with only the plate "
       "characters, no spaces and no other text. Indian plates have 2 letters, 2 digits, 1 to 3 letters, then 4 digits.")
P_E = ("Read the license plate in this image. If you cannot clearly read every character, reply exactly UNREADABLE and do not "
       "guess. Otherwise reply with only the plate characters, no spaces and no other text.")
P_GATE = "Look at this image of a vehicle license plate. Can you clearly read every character of the plate? Answer with only YES or NO."
proc = AutoProcessor.from_pretrained(M)
model = Qwen3VLForConditionalGeneration.from_pretrained(M, torch_dtype=torch.bfloat16, device_map="cuda")


def read(im, prompt, n=24):
    msgs = [{"role": "user", "content": [{"type": "image", "image": im}, {"type": "text", "text": prompt}]}]
    inp = proc.apply_chat_template(msgs, add_generation_prompt=True, tokenize=True, return_dict=True, return_tensors="pt").to(model.device)
    with torch.no_grad():
        out = model.generate(**inp, do_sample=False, max_new_tokens=n)
    txt = proc.batch_decode(out[:, inp["input_ids"].shape[1]:], skip_special_tokens=True)[0]
    txt = txt.strip().replace(" ", "")
    return "UNREADABLE" if "UNREADABLE" in txt.upper() else txt


rows = []
for p in sorted(glob.glob(os.path.join(CROPS, "*.png"))):
    im = Image.open(p).convert("RGB")
    big = im.resize((im.width * 3, im.height * 3), Image.LANCZOS)
    d = read(big, P_D)
    e = read(big, P_E)
    gate = read(big, P_GATE, 4).upper()
    g = read(big, P_FMT) if gate.startswith("YES") else "UNREADABLE"
    print(os.path.basename(p), "|", d, "|", e, "|", g, flush=True)
    rows.append({"crop_file": os.path.basename(p), "D_hint_unreadable": d, "E_base_unreadable": e, "G_gate": g})
with open(OUT, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=["crop_file", "D_hint_unreadable", "E_base_unreadable", "G_gate"])
    w.writeheader()
    w.writerows(rows)
print("saved:", OUT)