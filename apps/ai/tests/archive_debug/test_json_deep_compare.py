"""
Comparaison PROFONDE entre le JSON de reference (90.7% PFR)
et le JSON genere (77% PFR)
"""
import json
import sys
from pathlib import Path

# Fix encoding
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

print("="*80)
print("COMPARAISON PROFONDE: JSON Reference vs JSON Genere")
print("="*80)
print()

# Load JSONs
ref_path = Path(__file__).parent.parent / "output" / "cv_modele_content.json"
gen_path = Path(__file__).parent.parent / "output" / "cv_modele_NEW_PROMPT_fr_content.json"

# Check if NEW_PROMPT file exists
if not gen_path.exists():
    print(f"ERREUR: {gen_path.name} n'existe pas")
    print("Utilisation du test_direct_content.json a la place")
    gen_path = Path(__file__).parent.parent / "output" / "test_direct_content.json"

with open(ref_path, "r", encoding="utf-8") as f:
    ref = json.load(f)

with open(gen_path, "r", encoding="utf-8") as f:
    gen = json.load(f)

print(f"Reference: {ref_path.name} (PFR 90.7%)")
print(f"Genere: {gen_path.name} (PFR 77.0%)")
print()

# Deep comparison of ALL fields
print("1. CONTACT INFORMATION")
print("-"*80)
ref_contact = ref.get("contact_information", [])
gen_contact = gen.get("contact_information", [])

if ref_contact and gen_contact:
    rc = ref_contact[0]
    gc = gen_contact[0]

    for key in ["name", "address", "phone", "email"]:
        rv = rc.get(key, "")
        gv = gc.get(key, "")
        if len(rv) != len(gv):
            print(f"  {key}: {len(rv)} vs {len(gv)} chars (delta: {len(gv)-len(rv):+d})")
print()

# Work experience - DETAILED
print("2. WORK EXPERIENCE (DETAILED)")
print("-"*80)

ref_exp = ref.get("work_experience", [])
gen_exp = gen.get("work_experience", [])

for idx, (rexp, gexp) in enumerate(zip(ref_exp, gen_exp), 1):
    print(f"\nExperience #{idx}: {rexp.get('company', 'N/A')}")

    # Compare each field
    for field in ["date", "company", "location", "position", "duration"]:
        rv = rexp.get(field, "") or ""
        gv = gexp.get(field, "") or ""
        if len(rv) != len(gv):
            delta = len(gv) - len(rv)
            print(f"  {field}: '{rv}' vs '{gv}' (delta: {delta:+d})")

    # Bullets
    rbullets = rexp.get("bullets", [])
    gbullets = gexp.get("bullets", [])

    print(f"  Bullets: {len(rbullets)} vs {len(gbullets)}")
    for bidx, (rb, gb) in enumerate(zip(rbullets, gbullets), 1):
        delta = len(gb) - len(rb)
        print(f"    Bullet #{bidx}: {len(rb)} vs {len(gb)} chars (delta: {delta:+d})")
        if abs(delta) > 10:
            print(f"      REF: {rb[:80]}...")
            print(f"      GEN: {gb[:80]}...")

print()

# Education - DETAILED
print("3. EDUCATION (DETAILED)")
print("-"*80)

ref_edu = ref.get("education", [])
gen_edu = gen.get("education", [])

for idx, (redu, gedu) in enumerate(zip(ref_edu, gen_edu), 1):
    print(f"\nEducation #{idx}: {redu.get('institution', 'N/A')}")

    # Compare each field
    for field in ["year", "institution", "location", "degree", "major", "honors"]:
        rv = redu.get(field, "") or ""
        gv = gedu.get(field, "") or ""
        if rv != gv:
            delta = len(gv) - len(rv)
            if delta != 0:
                print(f"  {field}: {len(rv)} vs {len(gv)} chars (delta: {delta:+d})")
                if abs(delta) > 5:
                    print(f"    REF: '{rv}'")
                    print(f"    GEN: '{gv}'")

    # Coursework
    rcw = redu.get("coursework", [])
    gcw = gedu.get("coursework", [])

    if len(rcw) != len(gcw) or sum(len(c) for c in rcw) != sum(len(c) for c in gcw):
        print(f"  Coursework: {len(rcw)} items vs {len(gcw)} items")
        rcw_chars = sum(len(c) for c in rcw)
        gcw_chars = sum(len(c) for c in gcw)
        print(f"    Chars: {rcw_chars} vs {gcw_chars} (delta: {gcw_chars - rcw_chars:+d})")

print()

# Activities
print("4. ACTIVITIES & INTERESTS")
print("-"*80)

ref_act = ref.get("activities_interests", [])
gen_act = gen.get("activities_interests", [])

print(f"Items: {len(ref_act)} vs {len(gen_act)}")
for idx, (ra, ga) in enumerate(zip(ref_act, gen_act), 1):
    delta = len(ga) - len(ra)
    if delta != 0:
        print(f"  Activity #{idx}: {len(ra)} vs {len(ga)} chars (delta: {delta:+d})")
        print(f"    REF: {ra}")
        print(f"    GEN: {ga}")

print()

# Skills
print("5. SKILLS")
print("-"*80)

ref_it = ref.get("it_skills", [])
gen_it = gen.get("it_skills", [])
ref_lang = ref.get("language_skills", [])
gen_lang = gen.get("language_skills", [])

print(f"IT Skills: {len(ref_it)} vs {len(gen_it)}")
if ref_it != gen_it:
    print(f"  REF: {ref_it}")
    print(f"  GEN: {gen_it}")

print(f"\nLanguages: {len(ref_lang)} vs {len(gen_lang)}")
if ref_lang != gen_lang:
    print(f"  REF: {ref_lang}")
    print(f"  GEN: {gen_lang}")

print()
print("="*80)
print("FIN DE LA COMPARAISON")
print("="*80)
