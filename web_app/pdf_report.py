from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


def generate_pdf_report(report: dict) -> bytes:
    """Generate a ColdGuard PDF report from an analysis report dictionary."""

    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontSize=20,
        spaceAfter=6,
    )

    subtitle_style = ParagraphStyle(
        "ReportSubtitle",
        parent=styles["Normal"],
        alignment=TA_CENTER,
        fontSize=10,
        textColor=colors.grey,
        spaceAfter=18,
    )

    heading_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontSize=13,
        spaceBefore=12,
        spaceAfter=8,
    )

    body_style = ParagraphStyle(
        "ReportBody",
        parent=styles["BodyText"],
        fontSize=9,
        leading=13,
    )

    story = []

    # -------------------------------------------------- Header
    story.append(Paragraph("COLDGUARD", title_style))
    story.append(
        Paragraph(
            "Vaccine Potency Analysis Report",
            subtitle_style,
        )
    )

    # -------------------------------------------------- Basic information
    story.append(Paragraph("Analysis Summary", heading_style))

    summary_data = [
        ["Generated", str(report.get("generated_at", "N/A"))],
        ["Vaccine", str(report.get("vaccine_name", "N/A"))],
        ["Vaccine Type", str(report.get("vaccine_type", "N/A"))],
        ["Decision", str(report.get("decision", "N/A"))],
    ]

    summary_table = Table(summary_data, colWidths=[45 * mm, 125 * mm])

    summary_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#E8F5E9")),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("PADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )

    story.append(summary_table)

    # -------------------------------------------------- Potency
    story.append(Paragraph("Potency Analysis", heading_style))

    ci = report.get("ci_90", [None, None])

    potency_data = [
        ["Estimated Potency", f"{report.get('estimated_potency_pct', 0):.1f}%"],
        ["Confidence", f"{report.get('confidence', 0) * 100:.1f}%"],
        [
            "90% Credible Interval",
            f"{ci[0]:.1f}% - {ci[1]:.1f}%" if len(ci) == 2 else "N/A",
        ],
        [
            "Mean Kinetic Temperature",
            (
                f"{report['mkt_C']:.2f} °C"
                if report.get("mkt_C") is not None
                else "N/A"
            ),
        ],
    ]

    potency_table = Table(potency_data, colWidths=[65 * mm, 105 * mm])

    potency_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F5F5F5")),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("PADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )

    story.append(potency_table)

    # -------------------------------------------------- Explanation
    story.append(Paragraph("Analysis Explanation", heading_style))

    explanation = report.get(
        "natural_language_explanation",
        "No explanation available.",
    )

    story.append(Paragraph(str(explanation), body_style))

    # -------------------------------------------------- Degradation
    story.append(Paragraph("Degradation Assessment", heading_style))

    cause = report.get(
        "primary_degradation_cause",
        "Not specified",
    )

    story.append(
        Paragraph(
            f"<b>Primary degradation cause:</b> {cause}",
            body_style,
        )
    )

    # -------------------------------------------------- Data quality
    warnings = report.get("data_quality_warnings", [])

    story.append(Paragraph("Data Quality", heading_style))

    if warnings:
        for warning in warnings:
            story.append(
                Paragraph(f"• {warning}", body_style)
            )
    else:
        story.append(
            Paragraph(
                "No data quality warnings were reported.",
                body_style,
            )
        )

    freeze_count = report.get("freeze_events_count", 0)

    story.append(
        Paragraph(
            f"<b>Freeze events detected:</b> {freeze_count}",
            body_style,
        )
    )

    # -------------------------------------------------- Audit
    story.append(Paragraph("Audit Information", heading_style))

    audit_hash = report.get("audit_hash", "N/A")

    audit_data = [
        ["Audit Hash", str(audit_hash)],
    ]

    audit_table = Table(audit_data, colWidths=[45 * mm, 125 * mm])

    audit_table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("PADDING", (0, 0), (-1, -1), 7),
                ("FONTSIZE", (0, 0), (-1, -1), 7),
            ]
        )
    )

    story.append(audit_table)

    story.append(Spacer(1, 15))
    story.append(
        Paragraph(
            "Generated by ColdGuard — Vaccine Cold Chain Decision Support",
            subtitle_style,
        )
    )

    document.build(story)

    return buffer.getvalue()
