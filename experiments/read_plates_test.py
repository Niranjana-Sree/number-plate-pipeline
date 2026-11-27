# repo root: the folder that contains scripts/, eval/ and models/
import os as _os
ROOT = _os.path.abspath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), ".."))
import os, sys, csv, glob, torch
from PIL import Image, ImageFilter
from transformers import AutoProcessor, Qwen3VLForConditionalGeneration

M = _os.path.join(ROOT, 'models', 'Qwen3-VL-4B-Instruct')
CROPS = sys.argv[1]
OUT = sys.argv[2]
P_BASE = "Read the license plate in this image. Reply with only the plate characters, no spaces and no other text."
P_FMT = ("This is an Indian vehicle registration plate. Its format is: 2 letters for the state (for example TN), "
         "2 digits, 1 to 3 letters, then 4 digits. Read the plate. Reply with only the plate characters, no spaces and no other text.")
proc = AutoProcessor.from_pretrained(M)
model = Qwen3VLForConditionalGeneration.from_pretrained(M, torch_dtype=torch.bfloat16, device_map="cuda")


def read(im, prompt):
    msgs = [{"role": "user", "content": [{"type": "image", "image": im}, {"type": "text", "text": prompt}]}]
    inp = proc.apply_chat_template(msgs, add_generation_prompt=True, tokenize=True, return_dict=True, return_tensors="pt").to(model.device)
    with torch.no_grad():
        out = model.generate(**inp, do_sample=False, max_new_tokens=24)
    txt = proc.batch_decode(out[:, inp["input_ids"].shape[1]:], skip_special_tokens=True)[0]
    return txt.strip().replace(" ", "")


rows = []
for p in sorted(glob.glob(os.path.join(CROPS, "*.png"))):
    im = Image.open(p).convert("RGB")
    big = im.resize((im.width * 3, im.height * 3), Image.LANCZOS)
    sharp = big.filter(ImageFilter.UnsharpMask(radius=2, percent=150, threshold=2))
    a = read(big, P_BASE)
    b = read(big, P_FMT)
    c = read(sharp, P_BASE)
    print(os.path.basename(p), "|", a, "|", b, "|", c, flush=True)
    rows.append({"crop_file": os.path.basename(p), "A_base": a, "B_format_hint": b, "C_sharpen": c})
with open(OUT, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=["crop_file", "A_base", "B_format_hint", "C_sharpen"])
    w.writeheader()
    w.writerows(rows)
print("saved:", OUT)