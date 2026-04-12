"""
Unit tests for cover letter generation.

Tests:
- Job requirements extraction
- CV-to-job matching
- Cover letter generation
- Translation
- Layout PDF/DOCX
- Cost and timing validation
"""
import json
import os
import sys
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.cover_letter_generator import (
    extract_job_requirements,
    match_cv_to_job,
    generate_cover_letter_content,
    translate_cover_letter,
    generate_cover_letter
)
from app.cover_letter_layout import generate_cover_letter_files


# Mock data
MOCK_CV = {
    "contact_information": [
        {"type": "name", "value": "Fayed HANAFI"},
        {"type": "email", "value": "fayed.hanafi@example.com"},
        {"type": "phone", "value": "+33 6 12 34 56 78"},
        {"type": "location", "value": "Paris, France"}
    ],
    "education": [
        {
            "institution": "HEC Paris",
            "degree": "Master in Finance",
            "location": "Paris, France",
            "date": "Sep. 2020 - Jun. 2022",
            "duration": "2 years"
        }
    ],
    "work_experience": [
        {
            "company": "Rothschild & Co",
            "role": "Investment Banking Intern",
            "location": "Paris, France",
            "date": "Jun. 2021 - Dec. 2021",
            "duration": "6 months",
            "responsibilities": [
                "Supported execution of €450M pharmaceutical M&A transaction across 8 European markets",
                "Conducted DCF and LBO financial modeling, reducing comparables analysis time by 30%",
                "Prepared client presentations and pitch materials for senior bankers"
            ]
        },
        {
            "company": "Student Investment Fund",
            "role": "Analyst",
            "location": "Paris, France",
            "date": "Sep. 2020 - May. 2022",
            "duration": "20 months",
            "responsibilities": [
                "Led analysis of €2M equity investment in French fintech startup",
                "Achieved 22% IRR over 18 months through sector research and active monitoring",
                "Managed portfolio of 5 investments totaling €8M"
            ]
        }
    ],
    "it_skills": [
        {"name": "Financial Modeling (Excel)", "level": "Advanced"},
        {"name": "Python", "level": "Intermediate"},
        {"name": "Bloomberg Terminal", "level": "Advanced"},
        {"name": "VBA", "level": "Intermediate"}
    ],
    "language_skills": [
        {"language": "French", "level": "Native"},
        {"language": "English", "level": "Fluent"},
        {"language": "Arabic", "level": "Fluent"}
    ],
    "activities_interests": [
        "President of HEC Finance Society, organized 12 industry events with 500+ attendees"
    ]
}

MOCK_JOB_OFFER = """
Goldman Sachs - Investment Banking Analyst (M&A)
Paris, France

Goldman Sachs seeks an Investment Banking Analyst for our M&A team in Paris.

Requirements:
- 0-2 years of experience in finance or related field
- Strong financial modeling skills (DCF, LBO, comparable companies analysis)
- Excellent analytical and communication abilities
- Fluency in English and French required
- Knowledge of European markets preferred

Responsibilities:
- Conduct financial analysis, valuation, and modeling for M&A transactions
- Support deal execution from pitch to closing
- Prepare client presentations, pitch books, and transaction materials
- Collaborate with senior bankers on live transactions
- Perform due diligence and market research

We value meritocracy, intellectual rigor, client-first mindset, and teamwork.
Goldman Sachs offers an unparalleled training program and exposure to complex,
high-stakes transactions.
"""


def test_extract_job_requirements():
    """Test job requirements extraction."""
    print("\n" + "="*60)
    print("TEST 1: Extract Job Requirements")
    print("="*60)

    start = time.time()
    requirements = extract_job_requirements(MOCK_JOB_OFFER)
    elapsed = time.time() - start

    print(f"[OK] Extraction completed in {elapsed:.2f}s")
    print(f"\nExtracted requirements:")
    print(json.dumps(requirements, indent=2, ensure_ascii=False))

    # Validate
    assert requirements["company_name"] == "Goldman Sachs", "Company name mismatch"
    assert "Investment Banking Analyst" in requirements["position"], "Position mismatch"
    assert "Financial modeling" in [s for s in requirements["required_skills"]], "Missing key skill"
    assert requirements["experience_years"] in ["0-2", "0-3"], "Experience years incorrect"

    print(f"\n[OK] All validations passed")
    return requirements


def test_match_cv_to_job(job_requirements):
    """Test CV-to-job matching."""
    print("\n" + "="*60)
    print("TEST 2: Match CV to Job")
    print("="*60)

    matched = match_cv_to_job(MOCK_CV, job_requirements)

    print(f"\nMatched achievements: {len(matched['matched_achievements'])}")
    for i, ach in enumerate(matched['matched_achievements'], 1):
        print(f"\n{i}. {ach['company']} - {ach['role']}")
        print(f"   Skill matches: {ach['skill_match_count']}")
        print(f"   Responsibilities:")
        for resp in ach['responsibilities']:
            print(f"   - {resp}")

    print(f"\nMatched skills: {matched['matched_skills']}")
    print(f"Cultural fit signals: {matched['cultural_fit_signals']}")

    # Validate
    assert len(matched['matched_achievements']) >= 1, "No achievements matched"
    assert len(matched['matched_skills']) >= 1, "No skills matched"

    print(f"\n[OK] All validations passed")
    return matched


def test_generate_cover_letter_fr(job_requirements, matched_data):
    """Test cover letter generation in French."""
    print("\n" + "="*60)
    print("TEST 3: Generate Cover Letter (FR)")
    print("="*60)

    start = time.time()
    cover_letter = generate_cover_letter_content(
        cv_data=MOCK_CV,
        job_requirements=job_requirements,
        matched_data=matched_data,
        additional_notes="Passionné par M&A cross-border, admire culture méritocratique Goldman Sachs",
        language="fr"
    )
    elapsed = time.time() - start

    print(f"[OK] Generation completed in {elapsed:.2f}s")
    print(f"\nGenerated cover letter (FR):")
    print("="*60)
    print(cover_letter)
    print("="*60)

    # Validate
    word_count = len(cover_letter.split())
    paragraphs = [p for p in cover_letter.split("\n\n") if p.strip()]

    print(f"\nWord count: {word_count}")
    print(f"Paragraphs: {len(paragraphs)}")

    assert 250 <= word_count <= 450, f"Word count out of range: {word_count}"
    assert len(paragraphs) >= 4, f"Too few paragraphs: {len(paragraphs)}"
    assert "Goldman Sachs" in cover_letter, "Company name not mentioned"
    assert cover_letter.count("Goldman Sachs") >= 2, "Company mentioned <2 times"

    # Check for metrics
    has_percentage = "%" in cover_letter
    has_currency = "€" in cover_letter or "$" in cover_letter
    has_metrics = has_percentage or has_currency

    assert has_metrics, "No quantified metrics found"

    print(f"\n[OK] All validations passed")
    return cover_letter


def test_translate_cover_letter(cover_letter_fr):
    """Test cover letter translation FR -> EN."""
    print("\n" + "="*60)
    print("TEST 4: Translate Cover Letter (FR -> EN)")
    print("="*60)

    start = time.time()
    cover_letter_en = translate_cover_letter(
        cover_letter=cover_letter_fr,
        source_lang="fr",
        target_lang="en"
    )
    elapsed = time.time() - start

    print(f"[OK] Translation completed in {elapsed:.2f}s")
    print(f"\nTranslated cover letter (EN):")
    print("="*60)
    print(cover_letter_en)
    print("="*60)

    # Validate
    word_count_fr = len(cover_letter_fr.split())
    word_count_en = len(cover_letter_en.split())

    print(f"\nWord count FR: {word_count_fr}")
    print(f"Word count EN: {word_count_en}")
    print(f"Difference: {abs(word_count_en - word_count_fr)} words ({abs(word_count_en - word_count_fr) / word_count_fr * 100:.1f}%)")

    assert 250 <= word_count_en <= 450, f"Word count out of range: {word_count_en}"

    # Check translation quality
    assert "Goldman Sachs" in cover_letter_en, "Company name lost in translation"
    assert "Dear" in cover_letter_en or "Sincerely" in cover_letter_en, "English formulas not used"

    # Check metrics preserved
    if "€450M" in cover_letter_fr:
        assert "€450M" in cover_letter_en or "450M€" in cover_letter_en, "Metrics lost in translation"
    if "30%" in cover_letter_fr:
        assert "30%" in cover_letter_en, "Percentages lost in translation"

    print(f"\n[OK] All validations passed")
    return cover_letter_en


def test_generate_pdf_docx(cover_letter_fr, job_requirements):
    """Test PDF and DOCX generation."""
    print("\n" + "="*60)
    print("TEST 5: Generate PDF and DOCX")
    print("="*60)

    output_dir = Path(__file__).parent.parent / "output" / "test_cover_letter"

    result = generate_cover_letter_files(
        cover_letter=cover_letter_fr,
        cv_data=MOCK_CV,
        job_requirements=job_requirements,
        output_dir=str(output_dir),
        filename_base="test_cover_letter",
        language="fr",
        generate_docx=True
    )

    print(f"[OK] PDF generated: {result['pdf_path']}")
    print(f"   Page count: {result['page_count']}")
    print(f"   Word count: {result['word_count']}")

    if "docx_path" in result:
        print(f"[OK] DOCX generated: {result['docx_path']}")

    if result.get("warnings"):
        print(f"\n[WARN] Warnings:")
        for warning in result["warnings"]:
            print(f"   - {warning}")

    # Validate
    assert os.path.exists(result['pdf_path']), "PDF file not created"
    assert result['page_count'] == 1, f"Page count != 1: {result['page_count']}"

    if "docx_path" in result:
        assert os.path.exists(result['docx_path']), "DOCX file not created"

    print(f"\n[OK] All validations passed")
    return result


def test_full_pipeline():
    """Test complete pipeline with cost tracking."""
    print("\n" + "="*60)
    print("TEST 6: Full Pipeline (FR + EN)")
    print("="*60)

    start = time.time()

    result = generate_cover_letter(
        cv_data=MOCK_CV,
        job_offer=MOCK_JOB_OFFER,
        additional_notes="Passionné par M&A cross-border, admire culture méritocratique",
        language="fr",
        generate_both_languages=True
    )

    elapsed = time.time() - start

    print(f"\n[OK] Full pipeline completed in {elapsed:.2f}s")
    print(f"   Cost estimate: ${result['cost_estimate']:.4f}")
    print(f"   Word count FR: {result['word_count_fr']}")
    print(f"   Word count EN: {result['word_count_en']}")

    # Validate
    assert result['cover_letter_fr'] is not None, "FR cover letter not generated"
    assert result['cover_letter_en'] is not None, "EN cover letter not generated"
    assert result['cost_estimate'] < 0.020, f"Cost too high: ${result['cost_estimate']}"
    assert elapsed < 30, f"Generation too slow: {elapsed:.2f}s"

    print(f"\n[OK] All validations passed")

    # Generate PDFs
    output_dir = Path(__file__).parent.parent / "output" / "test_cover_letter_full"

    print(f"\nGenerating PDFs...")
    for lang, letter in [("fr", result['cover_letter_fr']), ("en", result['cover_letter_en'])]:
        pdf_result = generate_cover_letter_files(
            cover_letter=letter,
            cv_data=MOCK_CV,
            job_requirements=result['job_requirements'],
            output_dir=str(output_dir),
            filename_base="test_full_pipeline",
            language=lang,
            generate_docx=True
        )
        print(f"   [OK] {lang.upper()}: {pdf_result['pdf_path']}")

    return result


def run_all_tests():
    """Run all tests sequentially."""
    print("\n" + "="*80)
    print("COVER LETTER GENERATOR - UNIT TESTS")
    print("="*80)

    try:
        # Test 1: Extract job requirements
        job_requirements = test_extract_job_requirements()

        # Test 2: Match CV to job
        matched_data = test_match_cv_to_job(job_requirements)

        # Test 3: Generate cover letter FR
        cover_letter_fr = test_generate_cover_letter_fr(job_requirements, matched_data)

        # Test 4: Translate FR -> EN
        cover_letter_en = test_translate_cover_letter(cover_letter_fr)

        # Test 5: Generate PDF/DOCX
        pdf_result = test_generate_pdf_docx(cover_letter_fr, job_requirements)

        # Test 6: Full pipeline
        full_result = test_full_pipeline()

        print("\n" + "="*80)
        print("[OK] ALL TESTS PASSED")
        print("="*80)
        print(f"\nSummary:")
        print(f"- Job extraction: [OK]")
        print(f"- CV-to-job matching: [OK]")
        print(f"- Cover letter generation (FR): [OK]")
        print(f"- Translation (FR -> EN): [OK]")
        print(f"- PDF/DOCX generation: [OK]")
        print(f"- Full pipeline: [OK]")
        print(f"\nCost: ${full_result['cost_estimate']:.4f}")
        print(f"Time: {full_result['generation_time']:.2f}s")

        return True

    except AssertionError as e:
        print(f"\n[FAIL] TEST FAILED: {str(e)}")
        return False
    except Exception as e:
        print(f"\n[FAIL] ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
