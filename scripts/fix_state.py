import csv, re, sys

STATES = set("AN AP AR AS BR CG CH DD DL DN GA GJ HP HR JH JK KA KL LA LD MH ML MN MP MZ NL OD OR PB PY RJ SK TG TN TR TS UK UP WB".split())


def clean(text):
    return re.sub(r"[^A-Z0-9]", "", (text or "").upper()) # (patter , replacement char , input text)


def fix_state(text):
    t = clean(text)
    # slight hack for TN plates
    if len(t) >= 6 and t[:2] not in STATES and t[0] == "T" and t[1] in "MWHVU":
        return "TN" + t[2:]
    return t


if __name__ == "__main__":
    src, dst = sys.argv[1], sys.argv[2]
    rows = list(csv.DictReader(open(src, encoding="utf-8-sig")))
    n = 0
    with open(dst, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=["crop_file", "plate_text"])
        w.writeheader()
        for r in rows:
            new = fix_state(r["plate_text"])
            if new != clean(r["plate_text"]):
                n += 1
            w.writerow({"crop_file": r["crop_file"], "plate_text": new})
    print("state codes corrected:", n, "of", len(rows))