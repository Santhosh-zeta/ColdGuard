from web_app.pdf_report import generate_pdf_report


def test_generate_pdf_report():
    report = {
        "generated_at": "2026-09-14T17:40:00Z",
        "vaccine_type": "DPT",
        "vaccine_name": "DPT (Diphtheria-Pertussis-Tetanus)",
        "decision": "USE",
        "confidence": 1.0,
        "estimated_potency_pct": 89.0,
        "ci_90": [88.8, 89.0],
        "primary_degradation_cause": "Normal cold-chain storage",
        "natural_language_explanation": "Test explanation.",
        "audit_hash": "test-audit-hash",
        "posterior_summary": {},
        "mkt_C": 4.0,
        "data_quality_warnings": [],
        "freeze_events_count": 0,
    }

    pdf = generate_pdf_report(report)

    assert isinstance(pdf, bytes)
    assert pdf.startswith(b"%PDF")
    assert len(pdf) > 1000
