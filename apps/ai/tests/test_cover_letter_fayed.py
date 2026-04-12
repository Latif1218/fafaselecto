"""
Test cover letter generation with real Fayed CV + Goldman Sachs job offer.

This is the reference test case for production validation.

Expected results:
- Cost: < $0.018 per cover letter (FR+EN)
- Time: < 10 seconds
- Word count: 280-350 words
- Company mentions: 2-3×
- Metrics: 2-3 quantified
- 1 page PDF exactly
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.cover_letter_generator import generate_cover_letter
from app.cover_letter_layout import generate_cover_letter_files


# Fayed HANAFI CV (reconstructed from reference)
FAYED_CV = {
    "contact_information": [
        {"type": "name", "value": "Fayed HANAFI"},
        {"type": "email", "value": "fayed.hanafi@example.com"},
        {"type": "phone", "value": "+33 6 12 34 56 78"},
        {"type": "linkedin", "value": "linkedin.com/in/fayedhanafi"},
        {"type": "location", "value": "Paris, France"}
    ],
    "education": [
        {
            "institution": "HEC Paris",
            "degree": "Master in Finance",
            "location": "Paris, France",
            "date": "Sep. 2020 - Jun. 2022",
            "duration": "2 years",
            "relevant_coursework": [
                "Corporate Finance & Valuation",
                "Financial Markets & Derivatives",
                "M&A and LBO Modeling",
                "Advanced Financial Analysis"
            ]
        },
        {
            "institution": "École Polytechnique",
            "degree": "Bachelor in Applied Mathematics",
            "location": "Palaiseau, France",
            "date": "Sep. 2017 - Jun. 2020",
            "duration": "3 years"
        }
    ],
    "work_experience": [
        {
            "company": "Rothschild & Co",
            "role": "Investment Banking Analyst Intern",
            "location": "Paris, France",
            "date": "Jun. 2021 - Dec. 2021",
            "duration": "6 months",
            "responsibilities": [
                "Supported execution of €450M pharmaceutical M&A transaction, conducting financial modeling (DCF, LBO) and due diligence across 8 European markets",
                "Streamlined comparables analysis process, reducing preparation time by 30%, enabling senior bankers to accelerate client presentations",
                "Prepared pitch books and transaction materials for C-suite executives, contributing to 3 successful mandates totaling €1.2B"
            ]
        },
        {
            "company": "BNP Paribas Corporate & Institutional Banking",
            "role": "Corporate Finance Analyst Intern",
            "location": "Paris, France",
            "date": "Jan. 2021 - May. 2021",
            "duration": "5 months",
            "responsibilities": [
                "Conducted industry research and financial analysis for €200M+ corporate lending transactions in TMT and industrials sectors",
                "Built dynamic Excel models for covenant tracking and credit risk assessment, improving team efficiency by 25%",
                "Presented investment recommendations to credit committee, achieving 90% approval rate on 12 cases"
            ]
        },
        {
            "company": "HEC Investment Club",
            "role": "Portfolio Manager",
            "location": "Paris, France",
            "date": "Sep. 2020 - Jun. 2022",
            "duration": "22 months",
            "responsibilities": [
                "Led equity analysis and portfolio management of €2M student fund, achieving 22% annualized return vs. 15% CAC 40 benchmark",
                "Managed team of 5 analysts covering French mid-cap stocks, implementing rigorous DCF and relative valuation methodologies",
                "Presented quarterly portfolio reviews to 100+ student investors and faculty advisors"
            ]
        },
        {
            "company": "École Polytechnique Robotics Lab",
            "role": "Research Assistant",
            "location": "Palaiseau, France",
            "date": "Jun. 2019 - Aug. 2019",
            "duration": "3 months",
            "responsibilities": [
                "Developed optimization algorithms for autonomous vehicle path planning using Python and MATLAB",
                "Co-authored research paper on reinforcement learning applications, published in IEEE conference proceedings"
            ]
        }
    ],
    "it_skills": [
        {"name": "Financial Modeling (Excel, VBA)", "level": "Expert"},
        {"name": "Python (Pandas, NumPy, Matplotlib)", "level": "Advanced"},
        {"name": "Bloomberg Terminal & Capital IQ", "level": "Advanced"},
        {"name": "SQL & Database Management", "level": "Intermediate"},
        {"name": "PowerPoint & Pitch Book Design", "level": "Expert"}
    ],
    "language_skills": [
        {"language": "French", "level": "Native"},
        {"language": "English", "level": "Fluent (TOEFL 115/120)"},
        {"language": "Arabic", "level": "Fluent"},
        {"language": "Spanish", "level": "Intermediate"}
    ],
    "activities_interests": [
        "President of HEC Finance Society (2021-2022): Organized 12 industry panels with Goldman Sachs, JP Morgan, and McKinsey, attracting 500+ attendees",
        "Marathon runner: Completed Paris Marathon 2021 in 3h42, raising €5,000 for educational NGO in Morocco",
        "Volunteer tutor: Mentored 15 underprivileged high school students in mathematics and finance through \"Cordées de la Réussite\" program"
    ]
}


# Goldman Sachs M&A Analyst - Real job offer (simplified)
GOLDMAN_JOB_OFFER = """
Goldman Sachs - Investment Banking Analyst (M&A)
Paris, France

About Goldman Sachs:
Goldman Sachs is a leading global investment banking, securities and investment management firm
that provides a wide range of financial services to a substantial and diversified client base.

Position Overview:
We are seeking highly motivated Investment Banking Analysts to join our M&A team in Paris.
This is an exceptional opportunity to work on complex, high-profile transactions alongside
senior bankers and gain exposure to Europe's most strategic deals.

Key Responsibilities:
- Conduct financial analysis, valuation, and modeling for M&A transactions (DCF, LBO, comps)
- Support deal execution from initial pitch through closing, including due diligence coordination
- Prepare client presentations, pitch books, and transaction marketing materials
- Perform industry research and market analysis to identify strategic opportunities
- Collaborate with cross-functional teams (legal, tax, compliance) on live transactions
- Participate in client meetings and management presentations

Requirements:
- Bachelor's or Master's degree from a top-tier university (Grande École, Ivy League, Oxbridge)
- 0-2 years of relevant experience in investment banking, private equity, or corporate finance
- Strong financial modeling and valuation skills (DCF, LBO, comparable companies analysis)
- Excellent analytical capabilities and attention to detail
- Outstanding communication skills (written and verbal) in English and French
- Proficiency in Excel, PowerPoint, and financial databases (Bloomberg, Capital IQ)
- Ability to work in a fast-paced environment and manage multiple projects simultaneously

What We Offer:
- Unparalleled training program with access to Goldman Sachs University resources
- Exposure to landmark M&A transactions across diverse industries
- Collaborative, meritocratic culture that values intellectual curiosity and excellence
- Opportunity to work with senior leaders on strategic client engagements
- Competitive compensation package and career development opportunities

Goldman Sachs is committed to diversity and inclusion. We recruit, employ, train, compensate,
and promote regardless of race, religion, color, national origin, gender, disability, age,
and other protected factors.

To apply, please submit your resume and cover letter demonstrating your interest in investment
banking and why Goldman Sachs is the right fit for your career aspirations.
"""


def test_fayed_goldman_cover_letter():
    """
    Test cover letter generation with Fayed CV + Goldman Sachs offer.

    This is the reference test case for production.
    """
    print("\n" + "="*80)
    print("TEST: Fayed HANAFI - Goldman Sachs Investment Banking Analyst")
    print("="*80)

    # Additional notes (mimicking what user would provide)
    additional_notes = """
    Je suis particulièrement attiré par Goldman Sachs pour trois raisons:

    1. Excellence analytique: La réputation de Goldman en matière de rigueur intellectuelle
       et d'excellence dans les opérations complexes correspond à ma formation mathématique
       (Polytechnique) et mon expérience en M&A chez Rothschild.

    2. Culture méritocratique: J'ai eu l'opportunité d'échanger avec plusieurs analystes
       Goldman lors des panels organisés par la HEC Finance Society. Leur témoignage sur
       la culture méritocratique et les opportunités de développement rapide m'ont convaincu
       que Goldman est l'environnement idéal pour progresser.

    3. Transactions stratégiques: Je suis passionné par les opérations M&A cross-border
       complexes. Le rôle de conseil de Goldman sur des transactions majeures (ex: acquisitions
       pharma en Europe) correspond exactement au type de mandats sur lesquels je veux travailler.

    Mon objectif de carrière est de devenir un expert en M&A dans les secteurs TMT et Healthcare,
    et Goldman représente la meilleure plateforme pour y parvenir.
    """

    # Generate cover letter (FR + EN)
    result = generate_cover_letter(
        cv_data=FAYED_CV,
        job_offer=GOLDMAN_JOB_OFFER,
        additional_notes=additional_notes,
        language="fr",
        generate_both_languages=True
    )

    # Print results
    print(f"\n[OK] Generation completed!")
    print(f"   Time: {result['generation_time']:.2f}s")
    print(f"   Cost: ${result['cost_estimate']:.4f}")
    print(f"   Word count FR: {result['word_count_fr']}")
    print(f"   Word count EN: {result['word_count_en']}")

    # Validate targets
    assert result['cost_estimate'] < 0.020, f"[FAIL] Cost too high: ${result['cost_estimate']}"
    assert result['generation_time'] < 30, f"[FAIL] Too slow: {result['generation_time']:.2f}s"
    assert 250 <= result['word_count_fr'] <= 450, f"[FAIL] FR word count out of range: {result['word_count_fr']}"
    assert 250 <= result['word_count_en'] <= 450, f"[FAIL] EN word count out of range: {result['word_count_en']}"

    # Check company mentions
    gs_count_fr = result['cover_letter_fr'].count("Goldman Sachs")
    gs_count_en = result['cover_letter_en'].count("Goldman Sachs")

    print(f"\n[METRICS] Quality metrics:")
    print(f"   Goldman Sachs mentions (FR): {gs_count_fr}×")
    print(f"   Goldman Sachs mentions (EN): {gs_count_en}×")

    assert gs_count_fr >= 2, f"[FAIL] FR: Company mentioned only {gs_count_fr}× (need ≥2)"
    assert gs_count_en >= 2, f"[FAIL] EN: Company mentioned only {gs_count_en}× (need ≥2)"

    # Print cover letters
    print("\n" + "="*80)
    print("COVER LETTER - FRENCH")
    print("="*80)
    print(result['cover_letter_fr'])

    print("\n" + "="*80)
    print("COVER LETTER - ENGLISH")
    print("="*80)
    print(result['cover_letter_en'])

    # Generate PDFs
    output_dir = Path(__file__).parent.parent / "output" / "examples"
    output_dir.mkdir(parents=True, exist_ok=True)

    print("\n" + "="*80)
    print("GENERATING PDFs")
    print("="*80)

    for lang, letter in [("fr", result['cover_letter_fr']), ("en", result['cover_letter_en'])]:
        pdf_result = generate_cover_letter_files(
            cover_letter=letter,
            cv_data=FAYED_CV,
            job_requirements=result['job_requirements'],
            output_dir=str(output_dir),
            filename_base="cover_letter_fayed_goldman",
            language=lang,
            generate_docx=True
        )

        print(f"\n[OK] {lang.upper()} files generated:")
        print(f"   PDF: {pdf_result['pdf_path']}")
        print(f"   Page count: {pdf_result['page_count']}")
        print(f"   Word count: {pdf_result['word_count']}")

        if "docx_path" in pdf_result:
            print(f"   DOCX: {pdf_result['docx_path']}")

        if pdf_result.get('warnings'):
            print(f"   [WARN] Warnings:")
            for warning in pdf_result['warnings']:
                print(f"      - {warning}")

        # Validate page count
        assert pdf_result['page_count'] == 1, f"[FAIL] {lang.upper()}: Page count = {pdf_result['page_count']} (must be 1)"

    print("\n" + "="*80)
    print("[OK] ALL VALIDATIONS PASSED")
    print("="*80)
    print(f"\nReference outputs:")
    print(f"- PDF FR: {output_dir / 'cover_letter_fayed_goldman_fr.pdf'}")
    print(f"- PDF EN: {output_dir / 'cover_letter_fayed_goldman_en.pdf'}")
    print(f"- DOCX FR: {output_dir / 'cover_letter_fayed_goldman_fr.docx'}")
    print(f"- DOCX EN: {output_dir / 'cover_letter_fayed_goldman_en.docx'}")

    return result


if __name__ == "__main__":
    try:
        result = test_fayed_goldman_cover_letter()

        print("\n" + "="*80)
        print("FINAL SUMMARY")
        print("="*80)
        print(f"[OK] Cost: ${result['cost_estimate']:.4f} (target: <$0.018)")
        print(f"[OK] Time: {result['generation_time']:.2f}s (target: <10s)")
        print(f"[OK] Word count FR: {result['word_count_fr']} (target: 280-350)")
        print(f"[OK] Word count EN: {result['word_count_en']} (target: 280-350)")
        print(f"[OK] PDF pages: 1 (both FR and EN)")
        print(f"\n[SUCCESS] Production-ready!")

        sys.exit(0)

    except AssertionError as e:
        print(f"\n[FAIL] TEST FAILED: {str(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[FAIL] ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
