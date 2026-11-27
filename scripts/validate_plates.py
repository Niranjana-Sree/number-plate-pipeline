import csv, re, sys
IN, OUT = sys.argv[1], sys.argv[2]
STATES = set("AN AP AR AS BR CG CH DD DL DN GA GJ HP HR JH JK KA KL LA LD MH ML MN MP MZ NL OD OR PB PY RJ SK TG TN TR TS UK UP WB".split())
STD = re.compile(r"^([A-Z]{2})(\d{1,2})([A-Z]{1,3})(\d{1,4})$")
BH = re.compile(r"^\d{2}BH\d{4}[A-Z]{1,2}$")
rows = list(csv.DictReader(open(IN, encoding="utf-8-sig")))
counts = {}
for r in rows:
    clean = re.sub(r"[^A-Z0-9]", "", r["plate_text"].upper())
    if BH.match(clean):
        st, why = "valid", "BH series"
    elif len(set(clean)) <= 2 and len(clean) >= 5:
        st, why = "suspect", "repeated characters, likely invented"
    else:
        m = STD.match(clean)
        if m and len(m.group(4)) == 4:
            if m.group(1) in STATES:
                st, why = "valid", "format and state code ok"
            else:
                st, why = "check_state", "format ok but %s is not a known state code" % m.group(1)
        elif len(clean) < 8:
            st, why = "partial", "too short for a full plate (%d characters)" % len(clean)
        else:
            st, why = "invalid_format", "does not match the Indian plate pattern"
    r["plate_clean"], r["format_status"], r["reason"] = clean, st, why
    counts[st] = counts.get(st, 0) + 1
    print("%s -> %s | %s | %s" % (r["crop_file"], clean, st, why))
with open(OUT, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader(); w.writerows(rows)
print("summary:", counts, "| saved:", OUT)