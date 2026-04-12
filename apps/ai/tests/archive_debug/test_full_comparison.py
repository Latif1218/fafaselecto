"""
Comparaison exhaustive: Reference vs Genere
Identifie TOUTES les differences structurelles qui expliquent PFR 90.7% vs 78.1%
"""
import json
import sys
from pathlib import Path

# Fix encoding for Windows console
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

def count_chars_section(section_data):
    """Count total characters in a section."""
    if isinstance(section_data, list):
        total = 0
        for item in section_data:
            if isinstance(item, str):
                total += len(item)
            elif isinstance(item, dict):
                for value in item.values():
                    if isinstance(value, str):
                        total += len(value)
                    elif isinstance(value, list):
                        for sub_item in value:
                            if isinstance(sub_item, str):
                                total += len(sub_item)
        return total
    return 0

print("=" * 80)
print("COMPARAISON EXHAUSTIVE: R�f�rence vs G�n�r�")
print("=" * 80)
print()

# Load both JSONs
ref_path = Path(__file__).parent.parent / "output" / "cv_modele_content.json"
gen_path = Path(__file__).parent.parent / "output" / "test_direct_content.json"

with open(ref_path, "r", encoding="utf-8") as f:
    reference = json.load(f)

with open(gen_path, "r", encoding="utf-8") as f:
    generated = json.load(f)

print("Fichiers charg�s:")
print(f"  R�f�rence: cv_modele_content.json (PFR 90.7%)")
print(f"  G�n�r�: test_direct_content.json (PFR 78.1%)")
print()

# 1. WORK EXPERIENCE COMPARISON
print("1. WORK EXPERIENCE")
print("-" * 80)

ref_exp = reference.get("work_experience", [])
gen_exp = generated.get("work_experience", [])

ref_bullets = [b for exp in ref_exp for b in exp.get("bullets", [])]
gen_bullets = [b for exp in gen_exp for b in exp.get("bullets", [])]

ref_bullet_chars = sum(len(b) for b in ref_bullets)
gen_bullet_chars = sum(len(b) for b in gen_bullets)

print(f"Exp�riences: {len(ref_exp)} vs {len(gen_exp)}")
print(f"Bullets: {len(ref_bullets)} vs {len(gen_bullets)}")
print(f"Chars totaux bullets: {ref_bullet_chars} vs {gen_bullet_chars} (delta: {gen_bullet_chars - ref_bullet_chars:+d})")

# Detailed bullet comparison
print()
print("D�tail bullets:")
for i, (ref_b, gen_b) in enumerate(zip(ref_bullets, gen_bullets), 1):
    delta = len(gen_b) - len(ref_b)
    print(f"  Bullet #{i}: {len(ref_b)} vs {len(gen_b)} chars (delta: {delta:+d})")

print()

# 2. EDUCATION COMPARISON
print("2. EDUCATION")
print("-" * 80)

ref_edu = reference.get("education", [])
gen_edu = generated.get("education", [])

print(f"Entr�es: {len(ref_edu)} vs {len(gen_edu)}")

ref_cw_total = sum(len(edu.get("coursework", [])) for edu in ref_edu)
gen_cw_total = sum(len(edu.get("coursework", [])) for edu in gen_edu)

ref_cw_chars = sum(len(c) for edu in ref_edu for c in edu.get("coursework", []))
gen_cw_chars = sum(len(c) for edu in gen_edu for c in edu.get("coursework", []))

print(f"Coursework items: {ref_cw_total} vs {gen_cw_total}")
print(f"Coursework chars: {ref_cw_chars} vs {gen_cw_chars} (delta: {gen_cw_chars - ref_cw_chars:+d})")

# Detail per education
print()
print("D�tail par �ducation:")
for i, (ref_e, gen_e) in enumerate(zip(ref_edu, gen_edu), 1):
    ref_cw = ref_e.get("coursework", [])
    gen_cw = gen_e.get("coursework", [])
    ref_cw_c = sum(len(c) for c in ref_cw)
    gen_cw_c = sum(len(c) for c in gen_cw)

    print(f"  Edu #{i} ({ref_e.get('institution', 'N/A')[:30]}):")
    print(f"    Coursework: {len(ref_cw)} vs {len(gen_cw)} items")
    print(f"    Chars: {ref_cw_c} vs {gen_cw_c} (delta: {gen_cw_c - ref_cw_c:+d})")

    # Check degree/honors
    ref_degree = ref_e.get("degree", "") or ""
    gen_degree = gen_e.get("degree", "") or ""
    ref_honors = ref_e.get("honors", "") or ""
    gen_honors = gen_e.get("honors", "") or ""
    ref_major = ref_e.get("major", "") or ""
    gen_major = gen_e.get("major", "") or ""

    delta_degree = len(gen_degree) - len(ref_degree)
    delta_honors = len(gen_honors) - len(ref_honors)
    delta_major = len(gen_major) - len(ref_major)

    if delta_degree != 0:
        print(f"    Degree: {len(ref_degree)} vs {len(gen_degree)} chars (delta: {delta_degree:+d})")
    if delta_honors != 0:
        print(f"    Honors: {len(ref_honors)} vs {len(gen_honors)} chars (delta: {delta_honors:+d})")
    if delta_major != 0:
        print(f"    Major: {len(ref_major)} vs {len(gen_major)} chars (delta: {delta_major:+d})")

print()

# 3. ACTIVITIES
print("3. ACTIVITIES & INTERESTS")
print("-" * 80)

ref_act = reference.get("activities_interests", [])
gen_act = generated.get("activities_interests", [])

ref_act_chars = sum(len(a) for a in ref_act)
gen_act_chars = sum(len(a) for a in gen_act)

print(f"Items: {len(ref_act)} vs {len(gen_act)}")
print(f"Chars: {ref_act_chars} vs {gen_act_chars} (delta: {gen_act_chars - ref_act_chars:+d})")

if len(ref_act) == len(gen_act):
    for i, (ref_a, gen_a) in enumerate(zip(ref_act, gen_act), 1):
        delta = len(gen_a) - len(ref_a)
        print(f"  Activity #{i}: {len(ref_a)} vs {len(gen_a)} chars (delta: {delta:+d})")

print()

# 4. SKILLS
print("4. SKILLS (IT + LANGUAGES)")
print("-" * 80)

ref_it = reference.get("it_skills", [])
gen_it = generated.get("it_skills", [])
ref_lang = reference.get("language_skills", [])
gen_lang = generated.get("language_skills", [])

ref_it_chars = sum(len(s) for s in ref_it)
gen_it_chars = sum(len(s) for s in gen_it)
ref_lang_chars = sum(len(s) for s in ref_lang)
gen_lang_chars = sum(len(s) for s in gen_lang)

print(f"IT skills: {len(ref_it)} items ({ref_it_chars} chars) vs {len(gen_it)} items ({gen_it_chars} chars)")
print(f"  Delta: {gen_it_chars - ref_it_chars:+d} chars")

print(f"Languages: {len(ref_lang)} items ({ref_lang_chars} chars) vs {len(gen_lang)} items ({gen_lang_chars} chars)")
print(f"  Delta: {gen_lang_chars - ref_lang_chars:+d} chars")

print()

# 5. TOTAL COMPARISON
print("=" * 80)
print("SYNTH�SE TOTALE")
print("=" * 80)

ref_total = ref_bullet_chars + ref_cw_chars + ref_act_chars + ref_it_chars + ref_lang_chars
gen_total = gen_bullet_chars + gen_cw_chars + gen_act_chars + gen_it_chars + gen_lang_chars

print(f"Section              | R�f�rence  | G�n�r�    | Delta")
print("-" * 80)
print(f"Bullets              | {ref_bullet_chars:10d} | {gen_bullet_chars:9d} | {gen_bullet_chars - ref_bullet_chars:+6d}")
print(f"Coursework           | {ref_cw_chars:10d} | {gen_cw_chars:9d} | {gen_cw_chars - ref_cw_chars:+6d}")
print(f"Activities           | {ref_act_chars:10d} | {gen_act_chars:9d} | {gen_act_chars - ref_act_chars:+6d}")
print(f"IT Skills            | {ref_it_chars:10d} | {gen_it_chars:9d} | {gen_it_chars - ref_it_chars:+6d}")
print(f"Languages            | {ref_lang_chars:10d} | {gen_lang_chars:9d} | {gen_lang_chars - ref_lang_chars:+6d}")
print("-" * 80)
print(f"TOTAL                | {ref_total:10d} | {gen_total:9d} | {gen_total - ref_total:+6d}")
print()

pct_diff = ((gen_total - ref_total) / ref_total * 100) if ref_total > 0 else 0
print(f"Diff�rence: {pct_diff:+.1f}%")
print()

# Identify main culprits
print("PRINCIPALES DIFF�RENCES:")
deltas = {
    "Bullets": gen_bullet_chars - ref_bullet_chars,
    "Coursework": gen_cw_chars - ref_cw_chars,
    "Activities": gen_act_chars - ref_act_chars,
    "IT Skills": gen_it_chars - ref_it_chars,
    "Languages": gen_lang_chars - ref_lang_chars,
}

sorted_deltas = sorted(deltas.items(), key=lambda x: abs(x[1]), reverse=True)

for section, delta in sorted_deltas:
    if delta != 0:
        sign = "+" if delta > 0 else ""
        print(f"  {section:20s}: {sign}{delta:4d} chars ({delta/abs(ref_total - gen_total)*100 if ref_total != gen_total else 0:+.1f}% de la diff totale)")

print()
print("=" * 80)
